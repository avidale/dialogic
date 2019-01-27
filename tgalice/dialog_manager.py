

class BaseDialogManager:
    def respond(self, user_object, message_text):
        raise NotImplementedError()
        return updated_user_object, response, suggests, commands


class StupidDialogManager(BaseDialogManager):
    def respond(self, user_object, message_text):
        if message_text:
            response = "Вы сказали, '{}'".format(message_text.lower())
        else:
            response = "Вы не сказали ничего!"
        suggests = []
        updated_user_object = user_object
        commands = []
        return updated_user_object, response, suggests, commands
