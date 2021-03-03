import inspect
from collections.abc import Mapping


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
    def from_dict(cls, data, from_none=False):
        if data is None:
            if from_none:
                data = {}
            else:
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


class FreeSerializeable(Serializeable):
    """ A serializeable object that can accept and preserve arbitrary extra keys. """
    @classmethod
    def from_dict(cls, data, from_none=False):
        if isinstance(data, Mapping) and not isinstance(data, cls):
            arg_names = set(inspect.signature(cls.__init__).parameters)
            args = {k: v for k, v in data.items() if k in arg_names}
            other = {k: v for k, v in data.items() if k not in arg_names}
        else:
            args = data
            other = None
        result = super(FreeSerializeable, cls).from_dict(args, from_none=from_none)
        if result is not None:
            result._other = other
        return result

    def to_dict(self):
        result = super(FreeSerializeable, self).to_dict()
        if hasattr(self, '_other') and self._other:
            result.update(self._other)
        if '_other' in result:
            del result['_other']
        return result
