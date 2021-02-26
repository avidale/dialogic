import copy
from typing import Dict, Optional

import telebot
from ..dialog.serialized_message import SerializedMessage
from ..dialog.names import SOURCES
from tgalice.adapters.base import BaseAdapter, Context, Response, logger
from telebot.types import Message


class TelegramAdapter(BaseAdapter):
    SOURCE = SOURCES.TELEGRAM

    def __init__(self, suggest_cols=1, **kwargs):
        super(TelegramAdapter, self).__init__(**kwargs)
        self.suggest_cols = suggest_cols

    def make_context(self, message: Message, **kwargs) -> Context:
        uid = self.SOURCE + '__' + str(message.from_user.id)
        ctx = Context(
            user_object=None,
            message_text=message.text,
            metadata={},
            user_id=uid,
            session_id=uid,
            source=self.SOURCE,
            raw_message=message,
        )
        return ctx

    def make_response(self, response: Response, original_message=None, **kwargs):
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
            row_width = min(self.suggest_cols or 1, len(response.suggests))
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

    def serialize_context(self, context: Context, data=None, **kwargs) -> Optional[SerializedMessage]:
        message = context.raw_message
        if message.reply_to_message is not None:
            kwargs['reply_to_id'] = message.reply_to_message.message_id
        kwargs['message_id'] = message.message_id
        kwargs['username'] = message.chat.username
        serializable_message = {'message': str(message)}
        return super(TelegramAdapter, self).serialize_context(context=context, data=serializable_message, **kwargs)

    def serialize_response(self, data, context: Context, response: Response, **kwargs) -> Optional[SerializedMessage]:
        data = copy.deepcopy(data)
        message = context.raw_message
        kwargs['reply_to_id'] = message.message_id
        kwargs['username'] = message.chat.username
        # todo: maybe somehow get message_id for output messages
        if 'reply_markup' in data:
            data['reply_markup'] = data['reply_markup'].to_json()
        return super(TelegramAdapter, self).serialize_response(
            data=data,
            context=context,
            response=response,
            kwargs=kwargs
        )
