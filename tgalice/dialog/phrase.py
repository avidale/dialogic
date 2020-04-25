import random
from typing import Mapping

from tgalice.dialog import Response, names


class Phrase:
    """ This is a template for Response
    It has some methods to be parsed from configs.
    It generates a Response possibly by sampling options.
    """
    def __init__(self, name, text, exit=False, suggests=None):
        self.name = name
        if isinstance(text, list):
            self.texts = text
        else:
            self.texts = [text]
        self.exit = exit
        self.suggests = suggests or []
        # todo: read everything that can be found in response config

    def render(self, seed=None, additional_suggests=None):
        if seed is not None:
            random.seed(seed)
        text = random.choice(self.texts)
        resp = Response(text, suggests=self.suggests)
        resp.set_text(text)
        if self.exit:
            resp.commands.append(names.COMMANDS.EXIT)
        if additional_suggests:
            resp.suggests.extend(additional_suggests)
        return resp

    @classmethod
    def from_object(cls, obj):
        if isinstance(obj, str):
            return cls(name='unnamed', text=obj)
        elif isinstance(obj, Mapping):
            return cls(**obj)
        elif isinstance(obj, cls):
            return obj
        else:
            raise ValueError('Type {} cannot be converted to Phrase'.format(type(obj)))
