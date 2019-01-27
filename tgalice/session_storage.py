import copy


class BaseStorage:
    def __init__(self):
        self.dict = {}

    def get(self, key):
        return copy.deepcopy(self.dict.get(key, {}))

    def set(self, key, value):
        self.dict[key] = copy.deepcopy(value)
