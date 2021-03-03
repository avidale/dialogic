import random
import yaml

from collections.abc import Iterable

from ..nlu import basic_nlu
from ..nlu.matchers import make_matcher
from .base import CascadableDialogManager, Context, Response


class FAQDialogManager(CascadableDialogManager):
    """ This dialog manager tries to match the input message with one of the questions from its config,
    and if successful, gives the corresponding answer. """
    def __init__(self, config, matcher='tf-idf', *args, **kwargs):
        super(FAQDialogManager, self).__init__(*args, **kwargs)
        if isinstance(config, str):
            with open(config, 'r', encoding='utf-8') as f:
                self._cfg = yaml.safe_load(f)
        elif isinstance(config, Iterable):
            self._cfg = config
        else:
            raise ValueError('Config must be a filename or a list.')
        if isinstance(matcher, str):
            matcher = make_matcher(matcher)
        self.matcher = matcher
        self._q2i = {}
        self._i2a = {}
        self._i2s = {}
        question_keys = []
        question_labels = []
        for i, pair in enumerate(self._cfg):
            questions = self._extract_string_or_strings(pair, key='q')
            for q in questions:
                q2 = self._normalize(q)
                self._q2i[q2] = i
                question_keys.append(q2)
                question_labels.append(i)
            self._i2a[i] = self._extract_string_or_strings(pair, key='a')
            self._i2s[i] = self._extract_string_or_strings(pair, key='s', allow_empty=True)
        self.matcher.fit(question_keys, question_labels)

    def try_to_respond(self, ctx: Context):
        text = self._normalize(ctx.message_text)
        index, score = self.matcher.match(text)
        if index is None:
            return None
        response = random.choice(self._i2a[index])
        suggests = self._i2s.get(index, [])
        return Response(text=response, suggests=suggests, user_object=ctx.user_object).set_text(response)

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
