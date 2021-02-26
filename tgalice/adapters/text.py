from typing import Dict

from tgalice.dialog.names import SOURCES, REQUEST_TYPES
from tgalice.adapters.base import BaseAdapter, Context, Response, logger


class TextAdapter(BaseAdapter):
    SOURCE = SOURCES.TEXT

    def make_context(self, message: Dict, **kwargs) -> Context:
        ctx = Context(
            user_object=None,
            message_text=message,
            metadata={},
            user_id='the_text_user',
            session_id='the_text_session',
            source=self.SOURCE,
            raw_message=message,
        )
        return ctx

    def make_response(self, response: Response, original_message=None, **kwargs):
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
        return [result, response.has_exit_command]
