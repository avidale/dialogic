import copy
import json
import os

from . import database_utils


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
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)

    def load_dict(self, filename):
        with open(filename, 'r') as f:
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

    def __init__(self, database, collection_name='sessions'):
        super(MongoBasedStorage, self).__init__()
        # we assume that the database has PyMongo interface
        self._collection = database.get_collection(collection_name)
        database_utils.ensure_mongo_index(index_name=self.KEY_NAME, collection=self._collection)

    def get(self, key):
        result = self._collection.find_one({self.KEY_NAME: key})
        if result is None:
            return {}
        return result.get(self.VALUE_NAME, {})

    def set(self, key, value):
        self._collection.update_one(
            {self.KEY_NAME: key},
            {'$set': {self.VALUE_NAME: value}},
            upsert=True
        )
