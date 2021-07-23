from datetime import datetime


class SerializedMessage:
    # a base class for e.g. logging messages
    def __init__(self, text, user_id, from_user, timestamp=None, session_id=None, **kwargs):
        self.text = text
        self.user_id = user_id
        self.from_user = from_user
        self.timestamp = timestamp or str(datetime.utcnow())
        self.session_id = session_id
        self.kwargs = kwargs
        """
        Expected kwargs:
            text
            user_id
            message_id
            from_user
            username
            reply_to_id
            source
            data        (original message in Alice)
            label       (something like intent)
            request_id  (this id the same for request and response, useful for joining logs)
            handler     (name of the function that has produced the response)
        """

    def to_dict(self):
        result = {
            'text': self.text,
            'user_id': self.user_id,
            'from_user': self.from_user,
            'timestamp': self.timestamp,
            'session_id': self.session_id,
        }
        for k, v in self.kwargs.items():
            if k not in result:
                result[k] = v
        return result
