# coding: utf-8
import copy
import typing

from ..nlu import basic_nlu


class COMMANDS:
    EXIT = 'exit'


class Context:
    def __init__(self, user_object, message_text, metadata):
        self._user_object = copy.deepcopy(user_object)
        self.message_text = message_text
        self.metadata = metadata

    @property
    def user_object(self):
        return copy.deepcopy(self._user_object)


class Response:
    def __init__(self, text, suggests=None, commands=None, voice=None, user_object=None, confidence=0.5):
        self.text = text
        self.suggests = suggests or []
        self.commands = commands or []
        self.voice = voice if voice is not None else text
        self.updated_user_object = user_object
        self.confidence = confidence


class BaseDialogManager:
    """ This class defines the interface of dialog managers with a single `response` function. """
    def __init__(self, default_message='I dont\'t understand.'):
        self.default_message = default_message

    def respond(self, ctx: Context):
        return Response(text=self.default_message)


class CascadableDialogManager(BaseDialogManager):
    """ This interface allows dialog manager to have no answer - and to let other managers try.
    The `method try_to_respond` is like `respond`, but may also return None.
    It is expected to be used with CascadeDialogManager.
    """
    def __init__(self, *args, **kwargs):
        super(CascadableDialogManager, self).__init__(*args, **kwargs)

    def try_to_respond(self, ctx: Context) -> typing.Union[Response, None]:
        """ This method should return None or a valid Response """
        raise NotImplementedError()

    def respond(self, ctx):
        response = self.try_to_respond(ctx)
        if isinstance(response, Response):
            return response
        return Response(text=self.default_message)


class CascadeDialogManager(BaseDialogManager):
    """ This dialog manager tries multiple dialog managers in turn, and returns the first successful response. """
    def __init__(self, *managers):
        super(CascadeDialogManager, self).__init__()
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

    def try_to_respond(self, ctx: Context):
        if self.is_first_message(ctx):
            return Response(text=self.greeting_message)
        if self.is_like_help(ctx):
            return Response(text=self.help_message)
        if self.exit_message is not None and self.is_like_exit(ctx):
            return Response(text=self.exit_message, commands=[COMMANDS.EXIT])
        return None

    def is_first_message(self, context):
        if not context.message_text or context.message_text == '/start':
            return True
        if basic_nlu.like_help(context.message_text):
            return True
        return False

    def is_like_help(self, context):
        return basic_nlu.like_help(context.message_text)

    def is_like_exit(self, context):
        return basic_nlu.like_exit(context.message_text)
