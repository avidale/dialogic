# coding: utf-8

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
    def __init__(self, fixed_response='I always answer with this text.', fixed_suggests=None):
        self.fixed_response = fixed_response
        self.fixed_suggests = fixed_suggests or []

    def respond(self, user_object, message_text, metadata):
        updated_user_object = user_object
        response = self.fixed_response
        suggests = self.fixed_suggests
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
        if not context.message_text or context.message_text == '/start':
            return True
        if basic_nlu.like_help(context.message_text):
            return True
        return False

    def is_like_help(self, context):
        return basic_nlu.like_help(context.message_text)

    def is_like_exit(self, context):
        return basic_nlu.like_exit(context.message_text)
