

class COMMANDS:
    EXIT = 'exit'


class BaseDialogManager:
    def respond(self, user_object, message_text, metadata):
        updated_user_object = user_object
        response = 'Я не могу на это ответить.'
        suggests = []
        commands = []
        return updated_user_object, response, suggests, commands


class StupidDialogManager(BaseDialogManager):
    def respond(self, user_object, message_text, metadata):
        if message_text:
            response = "Вы сказали, '{}'".format(message_text.lower())
        else:
            response = "Вы не сказали ничего!"
        suggests = []
        updated_user_object = user_object
        commands = []
        return updated_user_object, response, suggests, commands
