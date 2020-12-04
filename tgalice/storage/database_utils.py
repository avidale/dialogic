import logging
import os

from collections.abc import Mapping

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


def get_boto_s3(
        service_name='s3',
        endpoint_url='https://storage.yandexcloud.net',
        aws_access_key_id=None,
        aws_access_key_id_env_name='AWS_ACCESS_KEY_ID',
        aws_secret_access_key=None,
        aws_secret_access_key_env_name='AWS_SECRET_ACCESS_KEY',
        region_name='ru-central1',
):
    import boto3
    session = boto3.session.Session()
    s3 = session.client(
        service_name=service_name,
        endpoint_url=endpoint_url,
        aws_access_key_id=aws_access_key_id or os.environ[aws_access_key_id_env_name],
        aws_secret_access_key=aws_secret_access_key or os.environ[aws_secret_access_key_env_name],
        region_name=region_name,
    )
    return s3


def fix_bson_keys(data, dot_symbol='~'):
    """ Replace dots in dict keys with other symbols, to comply with Pymongo checks """
    if isinstance(data, Mapping):
        result = {}
        for key, value in data.items():
            new_key = key
            if isinstance(key, str):
                if '.' in key:
                    logger.warning('Replacing a dot in key {} with {}'.format(key, dot_symbol))
                new_key = new_key.replace('.', dot_symbol)
            else:
                logger.warning('Replacing a key {} of type {} with its string representation'.format(key, type(key)))
                new_key = str(key)
            result[new_key] = fix_bson_keys(value, dot_symbol=dot_symbol)
        return result
    elif isinstance(data, list):
        return [fix_bson_keys(item, dot_symbol=dot_symbol) for item in data]
    else:
        return data
