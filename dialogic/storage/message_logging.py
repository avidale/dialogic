import copy
import logging

from datetime import datetime

from ..dialog.serialized_message import SerializedMessage
from dialogic.dialog import Context, Response
from dialogic.dialog.names import SOURCES, REQUEST_TYPES
from dialogic.storage.database_utils import get_mongo_or_mock, fix_bson_keys


try:
    import pymongo
except ModuleNotFoundError:
    pymongo = None


logger = logging.getLogger(__name__)


class BaseMessageLogger:
    def __init__(self, detect_pings=False, not_log_id=None, ignore_show=True):
        self.detect_pings = detect_pings
        self.not_log_id = not_log_id or set()
        self.ignore_show = ignore_show

    def log_context(self, context, **kwargs):
        raise DeprecationWarning(
            'This operation is no longer supported - please, use log_data method.'
        )

    def log_response(self, data, source, context=None, response=None, **kwargs):
        raise DeprecationWarning(
            'This operation is no longer supported - please, use log_data method.'
        )

    def log_message(self, message, source, context=None, response=None, **kwargs):
        raise DeprecationWarning(
            'This operation is no longer supported - please, use log_data method.'
        )

    def log_data(
            self,
            data: SerializedMessage,
            context: Context = None,
            response: Response = None,
            **kwargs
    ):
        if not data:
            return
        if response is not None and response.label is not None:
            data.kwargs['label'] = response.label
        if response is not None and response.handler is not None:
            data.kwargs['handler'] = response.handler
        if self.should_ignore_message(result=data, context=context, response=response):
            return
        self.save_a_message(data.to_dict())

    def is_like_ping(self, context=None):
        return context is not None and context.source == SOURCES.ALICE \
               and context.message_text == 'ping' and context.session_is_new()

    def should_ignore_message(
            self, result: SerializedMessage, context: Context = None, response: Response = None
    ) -> bool:
        if self.not_log_id is not None and result.user_id in self.not_log_id:
            # main reason: don't log pings from Yandex
            return True
        if self.detect_pings and self.is_like_ping(context):
            return True
        if self.ignore_show:
            if context.yandex and context.yandex.request and context.yandex.request.type == REQUEST_TYPES.SHOW_PULL:
                return True
        return False

    def save_a_message(self, message_dict):
        logger.warning('You are using a BaseMessageLogger that does not store messages. '
                       'Please extend it to save logs directly to a database.')
        logger.info(message_dict)


class MongoMessageLogger(BaseMessageLogger):
    def __init__(self, collection=None, database=None, collection_name='message_logs', write_concern=0, **kwargs):
        super(MongoMessageLogger, self).__init__(**kwargs)
        self.collection = collection
        if self.collection is None:
            if database is None:
                database = get_mongo_or_mock()
            if pymongo and not isinstance(write_concern, pymongo.write_concern.WriteConcern):
                write_concern = pymongo.write_concern.WriteConcern(w=write_concern)
            self.collection = database.get_collection(collection_name, write_concern=write_concern)

    def save_a_message(self, message_dict):
        self.collection.insert_one(fix_bson_keys(message_dict))
