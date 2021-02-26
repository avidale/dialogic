import re

from typing import Dict

from ..adapters.base import BaseAdapter, Context, Response
from ..dialog.names import SOURCES, COMMANDS


class SalutAdapter(BaseAdapter):
    SOURCE = SOURCES.SALUT

    def __init__(self, split_bubbles='\n\n', **kwargs):
        super(SalutAdapter, self).__init__(**kwargs)
        self.split_bubbles = split_bubbles

    def make_context(self, message: Dict, **kwargs) -> Context:
        metadata = {}

        user = message.get('uuid')
        payload = message.get('payload') or {}
        pm = payload.get('message')

        user_id = user.get('userId')

        message_text = (pm or {}).get('original_text') or ''

        metadata['new_session'] = payload.get('new_session')

        ctx = Context(
            user_object=None,
            message_text=message_text,
            metadata=metadata,
            user_id=user_id,
            source=self.SOURCE,
            raw_message=message,
        )

        # ctx.request_type = message['request'].get('type', REQUEST_TYPES.SIMPLE_UTTERANCE)
        # ctx.payload = message['request'].get('payload', {})

        # todo: add a structured Salut request
        return ctx

    def make_response(self, response: Response, original_message=None, **kwargs):
        original_message = original_message or {}
        original_payload = original_message.get('payload') or {}

        items = []

        if response.text:
            if self.split_bubbles:
                texts = response.text.split(self.split_bubbles)
            else:
                texts = [response.text]
            for t in texts:
                items.append({'bubble': {'text': t}})

        buttons = []
        if response.links:
            for s in response.links:
                buttons.append({'title': s['title'], 'action': {'deep_link': s['url'], 'type': 'deep_link'}})
        if response.suggests:
            for s in response.suggests:
                buttons.append({'title': s, 'action': {'text': s, 'type': 'text'}})

        # todo: add cards

        if response.voice:
            voice = re.sub('<.*>', ' ', response.voice).strip().replace('\n', ' ')
        else:
            voice = response.text

        payload = {
            'pronounceText': voice,
            # pronounceTextType
            # emotion
            'items': items,
            'device': original_payload.get('device'),
            'auto_listening': True,
            'finished': bool(COMMANDS.EXIT in response.commands),
            # intent
            # asr_hints
        }
        if buttons:
            payload['suggestions'] = {'buttons': buttons}

        result = {
            "messageName": "ANSWER_TO_USER",
            "sessionId": original_message.get('sessionId'),
            "messageId": original_message.get('messageId'),
            "uuid": original_message.get('uuid'),
            "payload": payload
        }

        return result
