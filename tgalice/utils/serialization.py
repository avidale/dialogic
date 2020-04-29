

def list_converter(cls):
    def converter(item):
        return [cls.from_dict(x) for x in (item or [])]
    return converter


def dict_converter(cls):
    def converter(item):
        return {k: cls.from_dict(v) for k, v in (item or {}).items()}
    return converter


def try_serialize(item):
    if hasattr(item, 'to_dict'):
        return item.to_dict()
    return item


class Serializeable:
    """ This mixin is used for easy conversion of structured objects from and to json """

    @classmethod
    def from_dict(cls, data):
        if data is None:
            return None
        if isinstance(data, cls):
            return data
        # assume all the heavy lifting is done by converters in the cls.__init__
        return cls(**data)

    def to_dict(self):
        result = {}
        for field_name, field in self.__dict__.items():
            if isinstance(field, list):
                field = [try_serialize(item) for item in field]
            elif isinstance(field, dict):
                field = {k: try_serialize(v) for k, v in field.items()}
            else:
                field = try_serialize(field)
            result[field_name] = field
        return result
