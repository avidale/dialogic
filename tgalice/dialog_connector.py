import telebot

from .session_storage import BaseStorage
from .dialog_manager.base import Response, Context


class SOURCES:
    TELEGRAM = 'telegram'
    ALICE = 'alice'
    TEXT = 'text'
    FACEBOOK = 'facebook'
    unknown_source_error_message = 'Source must be on of {"telegram", "alice", "text", "facebook"}'


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
        elif source == SOURCES.FACEBOOK:
            user_id = source + '__' + message['sender']['id']
            message_text = message.get('message', {}).get('text') or message.get('postback', {}).get('payload')
        elif source == SOURCES.TEXT:
            user_id = 'the_text_user'
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
                result['parse_mode'] = 'html'
                for l in response.links:
                    result['text'] += '\n<a href="{}">{}</a>'.format(l['url'], l['title'])
            if response.suggests:
                # todo: do smarter row width calculation
                row_width = min(self.tg_suggests_cols, len(response.suggests))
                result['reply_markup'] = telebot.types.ReplyKeyboardMarkup(row_width=row_width)
                result['reply_markup'].add(*[telebot.types.KeyboardButton(t) for t in response.suggests])
            else:
                result['reply_markup'] = telebot.types.ReplyKeyboardRemove(selective=False)
            if response.image_url:
                if 'multimedia' not in result:
                    result['multimedia'] = []
                media_type = 'document' if response.image_url.endswith('.gif') else 'photo'
                result['multimedia'].append({'type': media_type, 'content': response.image_url})
            if response.sound_url:
                if 'multimedia' not in result:
                    result['multimedia'] = []
                result['multimedia'].append({'type': 'audio', 'content': response.sound_url})
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
            if response.voice is not None and response.voice != response.text:
                result['response']['tts'] = response.voice
            buttons = response.links or []
            if response.suggests:
                buttons = buttons + [{'title': suggest} for suggest in response.suggests]
            for button in buttons:
                if not isinstance(button.get('hide'), bool):
                    button['hide'] = True
            result['response']['buttons'] = buttons
            if response.image_id:
                result['response']['card'] = {
                    'type': 'BigImage',
                    'image_id': response.image_id,
                    'description': response.text
                    # todo: enable 'title' and 'button' properties as well
                }
            return result
        elif source == SOURCES.FACEBOOK:
            result = {'text': response.text}
            if response.suggests or response.links:
                links = [{'type': 'web_url', 'title': l['title'], 'url': l['url']} for l in response.links]
                suggests = [{'type': 'postback', 'title': s, 'payload': s} for s in response.suggests]
                result = {
                    "attachment": {
                        "type": "template",
                        "payload": {
                            "template_type": "button",
                            "text": response.text,
                            "buttons": links + suggests
                        }
                    }
                }
            return result  # for bot.send_message(recipient_id, result)
        elif source == SOURCES.TEXT:
            result = response.text
            if response.voice is not None and response.voice != response.text:
                result = result + '\n[voice: {}]'.format(response.voice)
            if response.image_id:
                result = result + '\n[image: {}]'.format(response.image_id)
            if response.image_url:
                result = result + '\n[image: {}]'.format(response.image_url)
            if response.sound_url:
                result = result + '\n[sound: {}]'.format(response.sound_url)
            if len(response.links) > 0:
                result = result + '\n' + ', '.join(['[{}: {}]'.format(l['title'], l['url']) for l in response.links])
            if len(response.suggests) > 0:
                result = result + '\n' + ', '.join(['[{}]'.format(s) for s in response.suggests])
            if len(response.commands) > 0:
                result = result + '\n' + ', '.join(['{{{}}}'.format(c) for c in response.commands])
            return result, has_exit_command
        else:
            raise ValueError(SOURCES.unknown_source_error_message)
