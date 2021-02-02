import copy

import telebot

import tgalice.utils

from typing import Optional

from tgalice.storage.session_storage import BaseStorage
from tgalice.dialog_manager.base import Response, Context
from tgalice.dialog.names import COMMANDS, SOURCES
from tgalice.interfaces.yandex import YandexResponse
from tgalice.utils.content_manager import YandexImageAPI


class DialogConnector:
    """ This class provides unified interface for both Telegram and Alice applications """
    def __init__(
            self,
            dialog_manager,
            storage=None,
            log_storage=None,
            default_source=SOURCES.TELEGRAM,
            tg_suggests_cols=1,
            alice_native_state=False,
            image_manager: Optional[YandexImageAPI] = None,
    ):
        """
        paramaters:
        - alice_native_state: bool or 'user' or 'state'
        """
        self.dialog_manager = dialog_manager
        self.default_source = default_source
        self.storage = storage or BaseStorage()
        self.log_storage = log_storage  # noqa
        self.tg_suggests_cols = tg_suggests_cols
        self.alice_native_state = alice_native_state
        self.image_manager = image_manager

    def respond(self, message, source=None):
        # todo: support different triggers - not only messages, but calendar events as well
        context = self.make_context(message=message, source=source)
        old_user_object = copy.deepcopy(context.user_object)
        if self.log_storage is not None:
            self.log_storage.log_context(context)

        response = self.dialog_manager.respond(context)
        if response.updated_user_object is not None and response.updated_user_object != old_user_object:
            if source == SOURCES.ALICE and self.alice_native_state:
                pass  # user object is added right to the response
            else:
                self.set_user_object(context.user_id, response.updated_user_object)

        result = self.standardize_output(source=source, original_message=context.raw_message, response=response)
        if self.log_storage is not None:
            self.log_storage.log_response(data=result, context=context, source=context.source, response=response)
        return result

    def make_context(self, message, source=None):
        if source is None:
            source = self.default_source
        context = Context.from_raw(source=source, message=message)
        if source == SOURCES.ALICE and self.alice_native_state:
            state = message.get('state', {})
            if self.alice_native_state == 'session':
                user_object = state.get('session')
            elif self.alice_native_state == 'user':
                user_object = state.get('user')
                # for unauthorized users, use application state instead
                if message.get('session') and 'user' not in message['session']:
                    user_object = state.get('application')
            elif self.alice_native_state == 'application':
                user_object = state.get('application')
            else:
                user_object = state
        else:
            user_object = self.get_user_object(context.user_id)
        context.add_user_object(user_object)
        return context

    def get_user_object(self, user_id):
        if self.storage is None:
            return {}
        return self.storage.get(user_id)

    def set_user_object(self, user_id, user_object):
        if self.storage is None:
            raise NotImplementedError()
        self.storage.set(user_id, user_object)

    def standardize_output(self, source, original_message, response: Response):
        has_exit_command = False
        if response.commands:
            for command in response.commands:
                if command == COMMANDS.EXIT:
                    has_exit_command = True
                else:
                    raise NotImplementedError('Command "{}" is not implemented'.format(command))
        if source == SOURCES.TELEGRAM:
            if response.raw_response is not None:
                return response.raw_response
            result = {
                'text': response.text
            }
            if response.links is not None:
                result['parse_mode'] = 'html'
                for link in response.links:
                    result['text'] += '\n<a href="{}">{}</a>'.format(link['url'], link['title'])
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
            result['disable_web_page_preview'] = True
            return result
        elif source == SOURCES.ALICE:
            result = {
                "version": original_message['version'],
                "response": {
                    "end_session": has_exit_command,
                    "text": response.text
                }
            }
            if self.alice_native_state and response.updated_user_object:
                if self.alice_native_state == 'session':
                    result['session_state'] = response.updated_user_object
                elif self.alice_native_state == 'application':
                    result['application_state'] = response.updated_user_object
                elif self.alice_native_state == 'user':
                    if original_message.get('session') and 'user' not in original_message['session']:
                        result['application_state'] = response.updated_user_object
                    result['user_state_update'] = response.updated_user_object
                else:
                    if 'session' in response.updated_user_object:
                        result['session_state'] = response.updated_user_object['session']
                    if 'application' in response.updated_user_object:
                        result['application_state'] = response.updated_user_object['application']
                    if 'user' in response.updated_user_object:
                        result['user_state_update'] = response.updated_user_object['user']
            if response.raw_response is not None:
                if isinstance(response.raw_response, YandexResponse):
                    result = response.raw_response.to_dict()
                else:
                    result['response'] = response.raw_response
                return result
            if response.voice is not None and response.voice != response.text:
                result['response']['tts'] = response.voice
            buttons = response.links or []
            for button in buttons:
                # avoid cyrillic characters in urls - they are not supported by Alice
                if 'url' in button:
                    button['url'] = tgalice.utils.text.encode_uri(button['url'])
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
                }
            elif response.image_url and self.image_manager:
                image_id = self.image_manager.get_image_id_by_url(response.image_url)
                if image_id:
                    result['response']['card'] = {
                        'type': 'BigImage',
                        'image_id': image_id,
                        'description': response.text
                    }
            if response.gallery is not None:
                result['response']['card'] = response.gallery.to_dict()
            if response.image is not None:
                result['response']['card'] = response.image.to_dict()
            if response.show_item_meta is not None:
                result['response']['show_item_meta'] = response.show_item_meta
            return result
        elif source == SOURCES.FACEBOOK:
            if response.raw_response is not None:
                return response.raw_response
            result = {'text': response.text}
            if response.suggests or response.links:
                links = [{'type': 'web_url', 'title': link['title'], 'url': link['url']} for link in response.links]
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
                result = result + '\n' + ', '.join(
                    ['[{}: {}]'.format(link['title'], link['url']) for link in response.links]
                )
            if len(response.suggests) > 0:
                result = result + '\n' + ', '.join(['[{}]'.format(s) for s in response.suggests])
            if len(response.commands) > 0:
                result = result + '\n' + ', '.join(['{{{}}}'.format(c) for c in response.commands])
            return [result, has_exit_command]
        elif source == SOURCES.VK:
            # todo: instead of a dict, use a class object as a response
            # todo: add multimedia, etc.
            result = {
                'text': response.text,
            }
            if response.suggests or response.links:
                rows = []
                for i, link in enumerate(response.links):
                    if i % self.tg_suggests_cols == 0:
                        rows.append([])
                    rows[-1].append({'action': {'type': 'open_link', 'label': link['title'], 'link': link['url']}})
                for i, suggest in enumerate(response.suggests):
                    if i % self.tg_suggests_cols == 0:
                        rows.append([])
                    rows[-1].append({'action': {'type': 'text', 'label': suggest}})
                for row in rows:
                    for button in row:
                        label = button['action']['label']
                        if len(label) > 40:
                            button['action']['label'] = label[:37] + '...'
                result['keyboard'] = {
                    'one_time': True,
                    'buttons': rows,
                }
            return result
        else:
            raise ValueError(SOURCES.unknown_source_error_message)

    def serverless_alice_handler(self, alice_request, context):
        """ This method can be set as a hanlder if the skill is deployed as a Yandex.Cloud Serverless Function """
        return self.respond(alice_request, source=SOURCES.ALICE)
