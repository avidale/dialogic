import telebot

from .session_storage import BaseStorage
from .dialog_manager.base import Response, Context


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
        context = Context(user_object=user_object, message_text=message_text, metadata=metadata)
        response = self.dialog_manager.respond(context)
        if response.updated_user_object is not None and response.updated_user_object != user_object:
            self.set_user_object(user_id, response.updated_user_object)
        response = self.standardize_output(source, message, response)
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
            user_id = source + '__' + str(message.from_user.id)
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

    def standardize_output(self, source, original_message, response: Response):
        has_exit_command = False
        if response.commands:
            for command in response.commands:
                if command == self.COMMAND_EXIT:
                    has_exit_command = True
                else:
                    raise NotImplementedError('Command "{}" is not implemented'.format(command))
        if source == SOURCES.TELEGRAM:
            result = {
                'text': response.text
            }
            if response.links is not None:
                for l in response.links:
                    result['text'] += '\n{}:{}'.format(l['title'], l['url'])
            if response.suggests:
                # todo: do smarter row width calculation
                row_width = min(self.tg_suggests_cols, len(response.suggests))
                result['reply_markup'] = telebot.types.ReplyKeyboardMarkup(row_width=row_width)
                result['reply_markup'].add(*[telebot.types.KeyboardButton(t) for t in response.suggests])
            else:
                result['reply_markup'] = telebot.types.ReplyKeyboardRemove(selective=False)
            return result
        elif source == SOURCES.ALICE:
            result = {
                "version": original_message['version'],
                "session": original_message['session'],
                "response": {
                    "end_session": has_exit_command,
                    "text": response.text
                }
            }
            buttons = response.links or []
            if response.suggests:
                buttons = buttons + [{'title': suggest} for suggest in response.suggests]
            for button in buttons:
                if not isinstance(button.get('hide'), bool):
                    button['hide'] = True
            result['response']['buttons'] = buttons
            return result
        elif source == SOURCES.TEXT:
            result = response.text
            if len(response.links) > 0:
                result = result + '\n' + ', '.join(['[{}: {}]'.format(l['title'], l['url']) for l in response.links])
            if len(response.suggests) > 0:
                result = result + '\n' + ', '.join(['[{}]'.format(s) for s in response.suggests])
            if len(response.commands) > 0:
                result = result + '\n' + ', '.join(['{{{}}}'.format(c) for c in response.commands])
            return result, has_exit_command
        else:
            raise ValueError(SOURCES.unknown_source_error_message)
