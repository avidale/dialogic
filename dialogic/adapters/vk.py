from typing import Dict, Optional

from ..dialog.serialized_message import SerializedMessage
from ..dialog.names import SOURCES, REQUEST_TYPES
from ..adapters.base import BaseAdapter, Context, Response, logger


class VkAdapter(BaseAdapter):
    SOURCE = SOURCES.VK

    def __init__(self, suggest_cols=1, **kwargs):
        super(VkAdapter, self).__init__(**kwargs)
        self.suggest_cols = suggest_cols

    def make_context(self, message, **kwargs) -> Context:
        uid = self.SOURCE + '__' + str(message.user_id)
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
        # todo: instead of a dict, use a class object as a response
        # todo: add multimedia, etc.
        result = {
            'text': response.text,
        }
        if response.suggests or response.links:
            rows = []
            for i, link in enumerate(response.links):
                if i % self.suggest_cols == 0:
                    rows.append([])
                rows[-1].append({'action': {'type': 'open_link', 'label': link['title'], 'link': link['url']}})
            for i, suggest in enumerate(response.suggests):
                if i % self.suggest_cols == 0:
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

    def serialize_context(self, context: Context, data=None, **kwargs) -> Optional[SerializedMessage]:
        serializable_message = {'message': context.raw_message.to_json()}
        return super(VkAdapter, self).serialize_context(context=context, data=serializable_message, **kwargs)
