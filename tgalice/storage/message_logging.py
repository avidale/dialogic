import copy
import logging

from datetime import datetime
from telebot import types as teletypes

from tgalice.dialog import Context, Response
from tgalice.dialog.names import SOURCES
from tgalice.storage.database_utils import get_mongo_or_mock


logger = logging.getLogger(__name__)


class LoggedMessage:
    def __init__(self, text, user_id, from_user, **kwargs):
        self.text = text
        self.user_id = user_id
        self.from_user = from_user
        self.timestamp = str(datetime.utcnow())
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
        """

    def save_to_mongo(self, collection):
        collection.insert_one(self.to_dict())

    def to_dict(self):
        result = {
            'text': self.text,
            'user_id': self.user_id,
            'from_user': self.from_user,
            'timestamp': self.timestamp
        }
        for k, v in self.kwargs.items():
            if k not in result:
                result[k] = v
        return result

    @classmethod
    def from_context(cls, context: Context, **kwargs):
        serializable_message = context.raw_message
        if context.source == SOURCES.TELEGRAM:
            message = context.raw_message
            if message.reply_to_message is not None:
                kwargs['reply_to_id'] = message.reply_to_message.message_id
            kwargs['message_id'] = message.message_id
            kwargs['username'] = message.chat.username
            serializable_message = {'message': str(message)}
        return cls(
            text=context.message_text,
            user_id=context.user_id,
            from_user=True,
            data=serializable_message,
            source=context.source,
            **kwargs
        )

    @classmethod
    def from_response(cls, data, context: Context, response: Response, **kwargs):
        data = copy.deepcopy(data)
        if context.source == SOURCES.TELEGRAM:
            message = context.raw_message
            kwargs['reply_to_id'] = message.message_id
            kwargs['username'] = message.chat.username
            # todo: maybe somehow get message_id for output messages
            if 'reply_markup' in data:
                data['reply_markup'] = data['reply_markup'].to_json()
        return cls(
            text=response.text,
            user_id=context.user_id,
            from_user=False,
            data=data,
            source=context.source,
            **kwargs
        )


class BaseMessageLogger:
    def __init__(self, detect_pings=False, not_log_id=None):
        self.detect_pings = detect_pings
        self.not_log_id = not_log_id or set()

    def log_context(self, context, **kwargs):
        return self.log_message(message=context.raw_message, context=context, source=context.source, **kwargs)

    def log_response(self, data, source, context=None, response=None, **kwargs):
        return self.log_message(message=data, source=source, context=context, response=response, **kwargs)

    def log_message(self, message, source, context=None, response=None, **kwargs):
        if context is not None:
            if response is not None:
                msg = LoggedMessage.from_response(message, context=context, response=response)
            else:
                msg = LoggedMessage.from_context(context)
        else:
            return
        if response is not None and response.label is not None:
            msg.kwargs['label'] = response.label
        if self.not_log_id is not None and msg.user_id in self.not_log_id:
            # main reason: don't log pings from Yandex
            return
        if self.detect_pings and self.is_like_ping(context):
            return
        self.save_a_message(msg.to_dict())

    def is_like_ping(self, context=None):
        return context is not None and context.source == SOURCES.ALICE \
               and context.message_text == 'ping' and context.session_is_new()

    def save_a_message(self, message_dict):
        logger.info(message_dict)


class MongoMessageLogger(BaseMessageLogger):
    def __init__(self, collection=None, database=None, collection_name='message_logs', write_concern=0, **kwargs):
        super(MongoMessageLogger, self).__init__(**kwargs)
        self.collection = collection
        if self.collection is None:
            if database is None:
                database = get_mongo_or_mock()
            self.collection = database.get_collection(collection_name, write_concern=write_concern)

    def save_a_message(self, message_dict):
        self.collection.insert_one(message_dict)
