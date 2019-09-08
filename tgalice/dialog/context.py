import copy

from .names import REQUEST_TYPES, SOURCES


class Context:
    def __init__(
            self, user_object, message_text, metadata, user_id=None, source=None, raw_message=None,
            request_type=REQUEST_TYPES.SIMPLE_UTTERANCE, payload=None
    ):
        self._user_object = copy.deepcopy(user_object)
        self.message_text = message_text
        self.metadata = metadata
        self.user_id = user_id
        self.source = source
        self.raw_message = raw_message
        self.request_type = request_type
        self.payload = payload

    @property
    def user_object(self):
        # todo: make _user_object constant instead of copying it every time
        return copy.deepcopy(self._user_object)

    def add_user_object(self, user_object):
        self._user_object = copy.deepcopy(user_object)

    def session_is_new(self):
        # todo: define new session for non-Alice sources as well
        return bool(self.metadata.get('new_session'))

    @classmethod
    def from_raw(cls, source, message):
        metadata = {}
        if source == SOURCES.TELEGRAM:
            user_id = source + '__' + str(message.from_user.id)
            message_text = message.text
        elif source == SOURCES.ALICE:
            user_id = source + '__' + message['session']['user_id']
            message_text = message['request'].get('command', '')
            metadata['new_session'] = message.get('session', {}).get('new', False)
        elif source == SOURCES.FACEBOOK:
            user_id = source + '__' + message['sender']['id']
            message_text = message.get('message', {}).get('text', '')
        elif source == SOURCES.TEXT:
            user_id = 'the_text_user'
            message_text = message
        else:
            raise ValueError(SOURCES.unknown_source_error_message + ', got {} instead'.format(source))
        ctx = cls(
            user_object=None,
            message_text=message_text,
            metadata=metadata,
            user_id=user_id,
            source=source,
            raw_message=message
        )
        if source == SOURCES.ALICE:
            ctx.request_type = message['request'].get('type', REQUEST_TYPES.SIMPLE_UTTERANCE)
            ctx.payload = message['request'].get('payload', {})
        elif source == SOURCES.FACEBOOK:
            if not message.get('message', {}).get('text', ''):
                payload = message.get('postback', {}).get('payload')
                if payload is not None:
                    ctx.payload = payload
                    ctx.request_type = REQUEST_TYPES.BUTTON_PRESSED  # todo: check if it is really the case
                # todo: do something in case of attachments (message['message'].get('attachments'))
                # if user sends us a GIF, photo,video, or any other non-text item
        return ctx