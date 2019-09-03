import copy


class Context:
    def __init__(self, user_object, message_text, metadata, source=None, raw_message=None):
        self._user_object = copy.deepcopy(user_object)
        self.message_text = message_text
        self.metadata = metadata
        self.source = source
        self.raw_message = raw_message

    @property
    def user_object(self):
        # todo: make _user_object constant instead of copying it every time
        return copy.deepcopy(self._user_object)
