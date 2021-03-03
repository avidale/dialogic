from typing import Dict

from dialogic.dialog.names import SOURCES, REQUEST_TYPES
from dialogic.adapters.base import BaseAdapter, Context, Response, logger


class FacebookAdapter(BaseAdapter):
    SOURCE = SOURCES.FACEBOOK

    def make_context(self, message: Dict, **kwargs) -> Context:
        uid = self.SOURCE + '__' + message['sender']['id']
        ctx = Context(
            user_object=None,
            message_text=message.get('message', {}).get('text', ''),
            metadata={},
            user_id=uid,
            session_id=uid,
            source=self.SOURCE,
            raw_message=message,
        )

        if not message.get('message', {}).get('text', ''):
            payload = message.get('postback', {}).get('payload')
            if payload is not None:
                ctx.payload = payload
                ctx.request_type = REQUEST_TYPES.BUTTON_PRESSED  # todo: check if it is really the case
            # todo: do something in case of attachments (message['message'].get('attachments'))
            # if user sends us a GIF, photo,video, or any other non-text item

        return ctx

    def make_response(self, response: Response, original_message=None, **kwargs):
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
