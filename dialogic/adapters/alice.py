from typing import Dict, Optional

from ..adapters.base import BaseAdapter, Context, Response, logger
from ..dialog.names import SOURCES, REQUEST_TYPES, COMMANDS
from ..interfaces.yandex import YandexRequest, YandexResponse
from ..utils.text import encode_uri
from ..utils.content_manager import YandexImageAPI


class AliceAdapter(BaseAdapter):
    SOURCE = SOURCES.ALICE

    def __init__(self, native_state=False, image_manager: Optional[YandexImageAPI] = None, **kwargs):
        super(AliceAdapter, self).__init__(**kwargs)
        self.native_state = native_state
        self.image_manager: Optional[YandexImageAPI] = image_manager

    def make_context(self, message: Dict, **kwargs) -> Context:
        metadata = {}

        if set(message.keys()) == {'body'}:
            message = message['body']
        try:
            sess = message['session']
        except KeyError:
            raise KeyError(f'The key "session" not found in message among keys {list(message.keys())}.')
        if sess.get('user', {}).get('user_id'):
            # the new user_id, which is persistent across applications
            user_id = self.SOURCE + '_auth__' + sess['user']['user_id']
        else:
            # the old user id, that changes across applications
            user_id = self.SOURCE + '__' + sess['user_id']
        try:
            message_text = message['request'].get('command', '')
        except KeyError:
            raise KeyError(f'The key "request" not found in message among keys {list(message.keys())}.')
        metadata['new_session'] = message.get('session', {}).get('new', False)

        ctx = Context(
            user_object=None,
            message_text=message_text,
            metadata=metadata,
            user_id=user_id,
            session_id=sess.get('session_id'),
            source=self.SOURCE,
            raw_message=message,
        )

        ctx.request_type = message['request'].get('type', REQUEST_TYPES.SIMPLE_UTTERANCE)
        ctx.payload = message['request'].get('payload', {})
        try:
            ctx.yandex = YandexRequest.from_dict(message)
        except Exception as e:
            logger.warning('Could not deserialize Yandex request: got exception "{}".'.format(e))

        return ctx

    def make_response(self, response: Response, original_message=None, **kwargs):

        directives = {}
        if response.commands:
            for command in response.commands:
                if command == COMMANDS.REQUEST_GEOLOCATION:
                    directives[COMMANDS.REQUEST_GEOLOCATION] = {}

        result = {
            "version": original_message['version'],
            "response": {
                "end_session": response.has_exit_command,
                "text": response.text
            }
        }
        if self.native_state and response.updated_user_object:
            if self.native_state == 'session':
                result['session_state'] = response.updated_user_object
            elif self.native_state == 'application':
                result['application_state'] = response.updated_user_object
            elif self.native_state == 'user':
                if original_message.get('session') and 'user' not in original_message['session']:
                    result['application_state'] = response.updated_user_object
                result['user_state_update'] = response.updated_user_object
            else:
                if 'session' in response.updated_user_object:
                    result['session_state'] = response.updated_user_object['session']
                if 'application' in response.updated_user_object:
                    result['application_state'] = response.updated_user_object['application']
                if 'user' in response.updated_user_object:
                    result['user_state_update'] = response.updated_user_object['user']
        if response.raw_response is not None:
            if isinstance(response.raw_response, YandexResponse):
                result = response.raw_response.to_dict()
            else:
                result['response'] = response.raw_response
            return result
        if response.voice is not None and response.voice != response.text:
            result['response']['tts'] = response.voice.replace('\n', ' ')
        buttons = response.links or []
        for button in buttons:
            # avoid cyrillic characters in urls - they are not supported by Alice
            if 'url' in button:
                button['url'] = encode_uri(button['url'])
        if response.suggests:
            buttons = buttons + [{'title': suggest} for suggest in response.suggests]
        for button in buttons:
            if not isinstance(button.get('hide'), bool):
                button['hide'] = True
        result['response']['buttons'] = buttons
        if response.image_id:
            result['response']['card'] = {
                'type': 'BigImage',
                'image_id': response.image_id,
                'description': response.text
            }
        elif response.image_url and self.image_manager:
            image_id = self.image_manager.get_image_id_by_url(response.image_url)
            if image_id:
                result['response']['card'] = {
                    'type': 'BigImage',
                    'image_id': image_id,
                    'description': response.text
                }
        if response.gallery is not None:
            result['response']['card'] = response.gallery.to_dict()
        if response.image is not None:
            result['response']['card'] = response.image.to_dict()
        if response.show_item_meta is not None:
            result['response']['show_item_meta'] = response.show_item_meta
        if directives:
            result['response']['directives'] = directives
        return result

    def uses_native_state(self, context: Context) -> bool:
        """ Whether dialog state can be extracted directly from a context"""
        return bool(self.native_state)

    def get_native_state(self, context: Context) -> Optional[Dict]:
        """ Return native dialog state if it is possible"""
        if not self.native_state:
            return
        message = context.raw_message
        state = message.get('state', {})

        if self.native_state == 'session':
            user_object = state.get('session')
        elif self.native_state == 'user':
            user_object = state.get('user')
            # for unauthorized users, use application state instead
            if message.get('session') and 'user' not in message['session']:
                user_object = state.get('application')
        elif self.native_state == 'application':
            user_object = state.get('application')
        else:
            user_object = state
        return user_object
