# coding: utf-8
import random
import yaml

from collections import Iterable
from tgalice import basic_nlu


class COMMANDS:
    EXIT = 'exit'


class Context:
    def __init__(self, user_object, message_text, metadata):
        self.user_object = user_object
        self.message_text = message_text
        self.metadata = metadata
        # todo: compare old and new user objects


class Response:
    def __init__(self, response, suggests=None, commands=None):
        pass
    # todo: use this class instead of 4 outputs


class BaseDialogManager:
    """ This class defines the interface of dialog managers with a single `response` function. """
    def respond(self, user_object, message_text, metadata):
        updated_user_object = user_object
        response = 'I always answer with this text.'
        suggests = []
        commands = []
        return updated_user_object, response, suggests, commands


class CascadableDialogManager(BaseDialogManager):
    """ This interface allows dialog manager to have no answer - and to let other managers try.
    The `method try_to_respond` is like `respond`, but may also return None.
    It is expected to be used with CascadeDialogManager.
    """
    def __init__(self, *args, default_message='I don\'t understand', **kwargs):
        super(CascadableDialogManager, self).__init__(*args, **kwargs)
        self.default_message = default_message

    def try_to_respond(self, *args, **kwargs):
        raise NotImplementedError()

    def respond(self, user_object, message_text, metadata):
        response = self.try_to_respond(user_object, message_text, metadata)
        if response is not None:
            return response
        return user_object, self.default_message, [], []


class CascadeDialogManager(BaseDialogManager):
    """ This dialog manager tries multiple dialog managers in turn, and returns the first successful response. """
    def __init__(self, *managers):
        assert len(managers) > 0
        for manager in managers[:-1]:
            assert isinstance(manager, CascadableDialogManager)
        self.candidates = managers[:-1]
        assert isinstance(managers[-1], BaseDialogManager)
        self.final_candidate = managers[-1]

    def respond(self, *args, **kwargs):
        for manager in self.candidates:
            response = manager.try_to_respond(*args, **kwargs)
            if response is not None:
                return response
        return self.final_candidate.respond(*args, **kwargs)


class GreetAndHelpDialogManager(CascadableDialogManager):
    """ This dialog manager can be responsible for the first and the last messages, and for the help message. """
    def __init__(self, greeting_message, help_message, *args, exit_message=None, **kwargs):
        super(GreetAndHelpDialogManager, self).__init__(*args, **kwargs)
        self.greeting_message = greeting_message
        self.help_message = help_message
        self.exit_message = exit_message

    def try_to_respond(self, user_object, message_text, metadata):
        context = Context(user_object=user_object, message_text=message_text, metadata=metadata)
        if self.is_first_message(context):
            return user_object, self.greeting_message, [], []
        if self.is_like_help(context):
            return user_object, self.help_message, [], []
        if self.exit_message is not None and self.is_like_exit(context):
            return user_object, self.exit_message, [], [COMMANDS.EXIT]
        return None

    def is_first_message(self, context):
        if not context.message_text or context.message_text== '/start':
            return True
        if basic_nlu.like_help(context.message_text):
            return True
        return False

    def is_like_help(self, context):
        return basic_nlu.like_help(context.message_text)

    def is_like_exit(self, context):
        return basic_nlu.like_exit(context.message_text)


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
