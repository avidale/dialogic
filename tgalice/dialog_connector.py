import copy
from tgalice.session_storage import BaseStorage

class DialogConnector:
    COMMAND_EXIT = 'exit'
    """ This class provides unified interface for both Telegram and Alice applications """
    def __init__(self, dialog_manager, storage=None, default_source='telegram'):
        self.dialog_manager = dialog_manager
        self.default_source = default_source
        self.storage = storage or BaseStorage()

    def respond(self, message, source=None):
        # todo: support different triggers - not only messages, but calendar events as well
        if source is None:
            source = self.default_source
        user_id, message_text = self.standardize_input(source, message)
        user_object = self.get_user_object(user_id)
        # todo: maybe just make user_object frozen?
        old_user_object = copy.deepcopy(user_object)
        updated_user_object, response_text, suggests, response_commands = self.dialog_manager.respond(user_object, message_text)
        # todo: execute response_commands
        if updated_user_object != old_user_object:
            self.set_user_object(user_id, updated_user_object)
        response = self.standardize_output(source, message, response_text, response_commands, suggests)
        return response

    def get_user_object(self, user_id):
        if self.storage is None:
            return {}
        return self.storage.get(user_id)

    def set_user_object(self, user_id, user_object):
        if self.storage is None:
            raise NotImplementedError()
        self.storage.set(user_id, user_object)

    def standardize_input(self, source, message):
        if source == 'telegram':
            user_id = source + '__' + message.chat.username
            message_text = message.text
        elif source == 'alice':
            user_id = source + '__' + message['session']['user_id']
            message_text = message['request']['original_utterance']
        else:
            raise ValueError('Source must be on of {"telegram", "alice"}')
        return user_id, message_text

    def standardize_output(self, source, original_message, response_text, response_commands=None, suggests=None):
        if response_commands:
            for command in response_commands:
                if command != self.COMMAND_EXIT:
                    raise NotImplementedError('Command "{}" is not implemented'.format(command))
        else:
            response_commands = []
        if source == 'telegram':
            if suggests:
                raise NotImplementedError()
            return response_text
        elif source == 'alice':
            response = {
                "version": original_message['version'],
                "session": original_message['session'],
                "response": {
                    "end_session": bool(self.COMMAND_EXIT in response_commands),
                    "text": response_text
                }
            }
            if suggests:
                response['response']['buttons'] = [{'title': suggest, 'hide': True} for suggest in suggests]
            return response
        else:
            raise ValueError('Source must be on of {"telegram", "alice"}')
