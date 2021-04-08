import copy

from typing import Optional, Dict, Any, Tuple

from .storage.message_logging import BaseMessageLogger

from .adapters import (
    AliceAdapter, BaseAdapter, FacebookAdapter, TextAdapter, TelegramAdapter, VkAdapter, SalutAdapter
)

from dialogic.storage.session_storage import BaseStorage
from dialogic.dialog_manager.base import Response, Context
from dialogic.dialog.names import SOURCES
from dialogic.utils.content_manager import YandexImageAPI


class DialogConnector:
    """ This class provides unified interface for Telegram and Alice, and other applications """
    def __init__(
            self,
            dialog_manager,
            storage=None,
            log_storage: Optional[BaseMessageLogger] = None,
            default_source=SOURCES.TELEGRAM,
            tg_suggests_cols=1,
            alice_native_state=False,
            image_manager: Optional[YandexImageAPI] = None,
            adapters: Optional[Dict[str, BaseAdapter]] = None,
    ):
        """
        paramaters:
        - alice_native_state: bool or 'user' or 'state'
        """
        self.dialog_manager = dialog_manager
        self.default_source = default_source
        self.storage = storage or BaseStorage()
        self.log_storage: Optional[BaseMessageLogger] = log_storage  # noqa
        self.tg_suggests_cols = tg_suggests_cols
        self.alice_native_state = alice_native_state
        self.image_manager = image_manager
        self.adapters: Dict[str, BaseAdapter] = adapters or {}
        self._add_default_adapters()

    def _add_default_adapters(self):
        if SOURCES.ALICE not in self.adapters:
            self.adapters[SOURCES.ALICE] = AliceAdapter(
                native_state=self.alice_native_state,
                image_manager=self.image_manager,
            )
        if SOURCES.FACEBOOK not in self.adapters:
            self.adapters[SOURCES.FACEBOOK] = FacebookAdapter()
        if SOURCES.TEXT not in self.adapters:
            self.adapters[SOURCES.TEXT] = TextAdapter()
        if SOURCES.TELEGRAM not in self.adapters:
            self.adapters[SOURCES.TELEGRAM] = TelegramAdapter(suggest_cols=self.tg_suggests_cols)
        if SOURCES.VK not in self.adapters:
            self.adapters[SOURCES.VK] = VkAdapter()
        if SOURCES.SALUT not in self.adapters:
            self.adapters[SOURCES.SALUT] = SalutAdapter()

    def add_adapter(self, name: str, adapter: BaseAdapter):
        self.adapters[name] = adapter

    def respond(self, message, source=None) -> Any:
        ctx, resp, result = self.full_respond(message=message, source=source)
        return result

    def full_respond(self, message, source=None) -> Tuple[Context, Response, Any]:
        adapter = self.adapters.get(source)
        # todo: support different triggers - not only messages, but calendar events as well
        context = self.make_context(message=message, source=source)
        old_user_object = copy.deepcopy(context.user_object)
        if adapter and self.log_storage is not None:
            logged = adapter.serialize_context(context=context)
            if logged:
                self.log_storage.log_data(data=logged, context=context)

        response = self.dialog_manager.respond(context)
        if response.updated_user_object is not None and response.updated_user_object != old_user_object:
            if adapter and adapter.uses_native_state(context=context):
                pass  # user object is added right to the response
            else:
                self.set_user_object(context.user_id, response.updated_user_object)

        result = self.standardize_output(source=source, original_message=context.raw_message, response=response)
        if self.log_storage is not None:
            logged = self.adapters[source].serialize_response(data=result, context=context, response=response)
            if logged:
                self.log_storage.log_data(data=logged, context=context, response=response)
        return context, response, result

    def make_context(self, message, source=None):
        if source is None:
            source = self.default_source
        assert source in self.adapters, f'Source "{source}" is not in the list of dialog adapters ' \
                                        f'{list(self.adapters.keys())}.'
        adapter = self.adapters[source]
        context = adapter.make_context(message=message)

        if adapter.uses_native_state(context=context):
            user_object = adapter.get_native_state(context=context)
        else:
            user_object = self.get_user_object(context.user_id)
        context.add_user_object(user_object)
        return context

    def get_user_object(self, user_id):
        if self.storage is None:
            return {}
        return self.storage.get(user_id)

    def set_user_object(self, user_id, user_object):
        if self.storage is None:
            raise NotImplementedError()
        self.storage.set(user_id, user_object)

    def standardize_output(self, source, original_message, response: Response):

        assert source in self.adapters, f'Source "{source}" is not in the list of dialog adapters ' \
                                        f'{list(self.adapters.keys())}.'
        return self.adapters[source].make_response(response=response, original_message=original_message)

    def serverless_alice_handler(self, alice_request, context):
        """ This method can be set as a hanlder if the skill is deployed as a Yandex.Cloud Serverless Function """
        return self.respond(alice_request, source=SOURCES.ALICE)
