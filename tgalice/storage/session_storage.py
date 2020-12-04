import codecs
import copy
import json
import os

from storage.database_utils import fix_bson_keys
from tgalice.utils import database_utils


class BaseStorage:
    def __init__(self):
        self.dict = {}

    def get(self, key):
        return copy.deepcopy(self.dict.get(key, {}))

    def set(self, key, value):
        self.dict[key] = copy.deepcopy(value)


class FileBasedStorage(BaseStorage):
    def __init__(self, path='session_storage', multifile=True):
        super(FileBasedStorage, self).__init__()
        self.path = path
        self.multifile = multifile
        if not os.path.exists(path):
            if self.multifile:
                os.mkdir(path)
            else:
                self.dump_dict(path, {})

    def dump_dict(self, filename, data):
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def load_dict(self, filename):
        if not os.path.exists(filename):
            return {}
        with open(filename, 'r', encoding='utf-8') as f:
            result = json.load(f)
        return result

    def get(self, key):
        if self.multifile:
            return self.load_dict(os.path.join(self.path, key))
        else:
            return self.load_dict(self.path).get(key, {})

    def set(self, key, value):
        if self.multifile:
            self.dump_dict(os.path.join(self.path, key), value)
        else:
            # todo: enable some concurrency guarantees
            data = self.load_dict(self.path)
            data[key] = value
            self.dump_dict(self.path, data)


class MongoBasedStorage(BaseStorage):
    KEY_NAME = 'key'
    VALUE_NAME = 'value'

    def __init__(self, database=None, collection_name='sessions', collection=None):
        assert database or collection
        super(MongoBasedStorage, self).__init__()
        # we assume that the database has PyMongo interface
        self._collection = collection or database.get_collection(collection_name)
        database_utils.ensure_mongo_index(index_name=self.KEY_NAME, collection=self._collection)

    def get(self, key):
        result = self._collection.find_one({self.KEY_NAME: key})
        if result is None:
            return {}
        return result.get(self.VALUE_NAME, {})

    def set(self, key, value):
        value = fix_bson_keys(value)
        self._collection.update_one(
            {self.KEY_NAME: key},
            {'$set': {self.VALUE_NAME: value}},
            upsert=True
        )


class S3BasedStorage(BaseStorage):
    """ This wrapper is intended to work with a boto3 client - e.g. in Yandex.Cloud Object Storage. """
    def __init__(self, s3_client, bucket_name, prefix=''):
        super(BaseStorage, self).__init__()
        self.s3_client = s3_client
        self.bucket_name = bucket_name
        self.prefix = prefix

    def modify_key(self, key):
        return self.prefix + key

    def get(self, key):
        try:
            result = self.s3_client.get_object(Bucket=self.bucket_name, Key=self.modify_key(key))
            body = result['Body']
            reader = codecs.getreader("utf-8")
            return json.load(reader(body))
        except Exception as e:
            if hasattr(e, 'response') and e.response.get('Error', {}).get('Code') == 'NoSuchKey':
                return {}
            else:
                raise e

    def set(self, key, value):
        self.s3_client.put_object(Bucket=self.bucket_name, Key=self.modify_key(key), Body=json.dumps(value))
