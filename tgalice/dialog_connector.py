import copy
import telebot

from .session_storage import BaseStorage


class SOURCES:
    TELEGRAM = 'telegram'
    ALICE = 'alice'
    TEXT = 'text'
    unknown_source_error_message = 'Source must be on of {"telegram", "alice", "text"}'


class DialogConnector:
    COMMAND_EXIT = 'exit'
    """ This class provides unified interface for both Telegram and Alice applications """
    def __init__(self, dialog_manager, storage=None, default_source='telegram', tg_suggests_cols=1):
        self.dialog_manager = dialog_manager
        self.default_source = default_source
        self.storage = storage or BaseStorage()
        self.tg_suggests_cols = tg_suggests_cols

    def respond(self, message, source=None):
        # todo: support different triggers - not only messages, but calendar events as well
        if source is None:
            source = self.default_source
        user_id, message_text, metadata = self.standardize_input(source, message)
        user_object = self.get_user_object(user_id)
        old_user_object = copy.deepcopy(user_object)
        updated_user_object, response_text, suggests, response_commands = self.dialog_manager.respond(
            user_object, message_text, metadata
        )
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
        metadata = {}
        if source == SOURCES.TELEGRAM:
            user_id = source + '__' + message.chat.username
            message_text = message.text
        elif source == SOURCES.ALICE:
            user_id = source + '__' + message['session']['user_id']
            message_text = message['request']['original_utterance']
            metadata['new_session'] = message.get('session', {}).get('new', False)
        elif source == SOURCES.TEXT:
            user_id = '0'
            message_text = message
        else:
            raise ValueError(SOURCES.unknown_source_error_message)
        return user_id, message_text, metadata

    def standardize_output(self, source, original_message, response_text, response_commands=None, suggests=None):
        has_exit_command = False
        if response_commands:
            for command in response_commands:
                if command == self.COMMAND_EXIT:
                    has_exit_command = True
                else:
                    raise NotImplementedError('Command "{}" is not implemented'.format(command))
        else:
            response_commands = []
        if source == SOURCES.TELEGRAM:
            response = {
                'text': response_text
            }
            if suggests:
                # todo: do smarter row width calculation
                row_width = min(self.tg_suggests_cols, len(suggests))
                response['reply_markup'] = telebot.types.ReplyKeyboardMarkup(row_width=row_width)
                response['reply_markup'].add(*[telebot.types.KeyboardButton(t) for t in suggests])
            else:
                response['reply_markup'] = telebot.types.ReplyKeyboardRemove(selective=False)
            return response
        elif source == SOURCES.ALICE:
            response = {
                "version": original_message['version'],
                "session": original_message['session'],
                "response": {
                    "end_session": has_exit_command,
                    "text": response_text
                }
            }
            if suggests:
                response['response']['buttons'] = [{'title': suggest, 'hide': True} for suggest in suggests]
            return response
        elif source == SOURCES.TEXT:
            response = response_text
            if suggests is not None and len(suggests) > 0:
                response = response + '\n' + ', '.join(['[{}]'.format(s) for s in suggests])
            if response_commands is not None and len(response_commands) > 0:
                response = response + '\n' + ', '.join(['{{{}}}'.format(c) for c in response_commands])
            return response, has_exit_command
        else:
            raise ValueError(SOURCES.unknown_source_error_message)
