
def ensure_mongo_index(index_name, collection, unique=False, index_type='hashed'):
    if index_name not in collection.index_information():
        collection.create_index([(index_name, index_type)], unique=unique)
