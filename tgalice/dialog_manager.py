import random
import yaml

from collections import Iterable
from tgalice.basic_nlu import fast_normalize


class COMMANDS:
    EXIT = 'exit'


class BaseDialogManager:
    def respond(self, user_object, message_text, metadata):
        updated_user_object = user_object
        response = 'Я не могу на это ответить.'
        suggests = []
        commands = []
        return updated_user_object, response, suggests, commands


class RepeaterDialogManager(BaseDialogManager):
    def respond(self, user_object, message_text, metadata):
        if message_text:
            response = "Вы сказали, '{}'".format(message_text.lower())
        else:
            response = "Вы не сказали ничего!"
        suggests = []
        updated_user_object = user_object
        commands = []
        return updated_user_object, response, suggests, commands


class FAQDialogManager(BaseDialogManager):
    def __init__(self, config, matcher='exact'):
        if isinstance(config, str):
            with open(config, 'r', encoding='utf-8') as f:
                self._cfg = yaml.load(f)
        elif isinstance(config, Iterable):
            self._cfg = config
        else:
            raise ValueError('Config must be a filename or a list.')
        if matcher != 'exact':
            raise ValueError('Non-exact matching is not supported yet.')
        self._q2i = {}
        self._i2a = {}
        self._i2s = {}
        for i, pair in enumerate(self._cfg):
            questions = self._extract_string_or_strings(pair, key='q')
            for q in questions:
                self._q2i[self._normalize(q)] = i
            self._i2a[i] = self._extract_string_or_strings(pair, key='a')
            self._i2s[i] = self._extract_string_or_strings(pair, key='s', allow_empty=True)

    def respond(self, user_object, message_text, metadata):
        text = self._normalize(message_text)
        suggests = []
        commands = []
        if text not in self._q2i:
            response = 'Я вас не понимаю.'
        else:
            index = self._q2i[text]
            response = random.choice(self._i2a[index])
            suggests.extend(self._i2s.get(index, []))
        return user_object, response, suggests, commands

    @staticmethod
    def _extract_string_or_strings(data, key, allow_empty=False):
        if key not in data:
            if allow_empty:
                return []
            raise ValueError('The question "{}" has no "{}" key.'.format(data, key))
        inputs = data[key]
        if isinstance(inputs, str):
            result = [inputs]
        elif isinstance(inputs, Iterable):
            if not all(isinstance(i, str) for i in inputs):
                raise ValueError('The list "{}" does not consist of strings.'.format(inputs))
            result = inputs
        else:
            raise ValueError('The question "{}" is not a string or list.'.format(data))
        return result

    def _normalize(self, text):
        return fast_normalize(text)
