import copy
import logging
import uuid

from typing import Optional

from .names import REQUEST_TYPES, SOURCES
from tgalice.interfaces.yandex import YandexRequest


logger = logging.getLogger(__name__)


class Context:
    def __init__(
            self, user_object, message_text, metadata, request_id=None, user_id=None, source=None, raw_message=None,
            request_type=REQUEST_TYPES.SIMPLE_UTTERANCE, payload=None, yandex=None,
            session_id=None,
    ):
        self._user_object = copy.deepcopy(user_object)
        self.message_text = message_text
        self.metadata = metadata
        self.request_id = request_id or str(uuid.uuid1())
        self.user_id = user_id
        self.session_id = session_id
        self.source = source
        self.raw_message = raw_message
        self.request_type = request_type
        self.payload = payload
        self.yandex: Optional[YandexRequest] = yandex

    @property
    def user_object(self):
        # todo: make this object explicitly frozen
        return self._user_object

    def add_user_object(self, user_object):
        self._user_object = copy.deepcopy(user_object)

    def session_is_new(self):
        # todo: define new session for non-Alice sources as well
        return bool(self.metadata.get('new_session'))

    @classmethod
    def from_raw(cls, source, message):
        raise DeprecationWarning('This method is not used anymore. Please use the adapters subpackage instead.')
