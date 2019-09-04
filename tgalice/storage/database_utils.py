import logging
import os

logger = logging.getLogger(__name__)


def get_mongo_or_mock(mongodb_uri=None, mongodb_uri_env_name='MONGODB_URI'):
    if mongodb_uri is None:
        mongodb_uri = os.environ.get(mongodb_uri_env_name)
    if mongodb_uri:
        from pymongo import MongoClient
        mongo_client = MongoClient(mongodb_uri)
        mongo_db = mongo_client.get_default_database()
    else:
        logging.warning('Did not found mongodb uri, trying to load mongomock instead. '
                        'This storage is not persistable and may cause problems in production; '
                        'please use it for testing only.')
        import mongomock
        mongo_client = mongomock.MongoClient()
        mongo_db = mongo_client.db
    return mongo_db
