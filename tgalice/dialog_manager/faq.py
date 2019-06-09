import random
import yaml

from collections import Iterable
from tgalice.nlu import basic_nlu
from tgalice.dialog_manager.base import CascadableDialogManager


class FAQDialogManager(CascadableDialogManager):
    """ This dialog manager tries to match the input message with one of the questions from its config,
    and if successful, gives the corresponding answer. """
    def __init__(self, config, matcher='exact', *args, **kwargs):
        super(FAQDialogManager, self).__init__(*args, **kwargs)
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

    def try_to_respond(self, user_object, message_text, metadata):
        text = self._normalize(message_text)
        if text not in self._q2i:
            return None
        commands = []
        index = self._q2i[text]
        response = random.choice(self._i2a[index])
        suggests = self._i2s.get(index, [])
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
        return basic_nlu.fast_normalize(text)
