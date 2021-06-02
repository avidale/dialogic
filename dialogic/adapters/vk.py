import copy
from typing import Optional

from ..dialog.serialized_message import SerializedMessage
from ..dialog.names import SOURCES
from ..adapters.base import BaseAdapter, Context, Response


class VkAdapter(BaseAdapter):
    SOURCE = SOURCES.VK

    def __init__(
            self,
            suggest_cols=1, suggest_screen=32, suggest_margin=1, suggest_max_len=40,
            suggest_max_cols=5, suggest_max_rows=10,
            **kwargs
    ):
        super(VkAdapter, self).__init__(**kwargs)
        self.suggest_cols = suggest_cols
        self.suggest_screen = suggest_screen
        self.suggest_margin = suggest_margin
        self.suggest_max_len = suggest_max_len
        self.suggest_max_cols = suggest_max_cols
        self.suggest_max_rows = suggest_max_rows

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
            buttons = []
            for i, link in enumerate(response.links):
                buttons.append({'action': {'type': 'open_link', 'label': link['title'], 'link': link['url']}})
            for i, suggest in enumerate(response.suggests):
                buttons.append({'action': {'type': 'text', 'label': suggest}})

            rows = []
            row_width = 0
            for i, button in enumerate(buttons):
                if self.suggest_cols == 'auto':
                    extra_width = len(button['action']['label']) + self.suggest_margin * 2
                    if len(rows) == 0 or row_width > 0 and row_width + extra_width > self.suggest_screen \
                            or len(rows[-1]) >= self.suggest_max_cols:
                        rows.append([])
                        row_width = extra_width
                    else:
                        row_width += extra_width
                else:
                    if i % self.suggest_cols == 0:
                        rows.append([])
                rows[-1].append(button)

            for row in rows:
                for button in row:
                    label = button['action']['label']
                    if len(label) > self.suggest_max_len:
                        button['action']['label'] = label[:(self.suggest_max_len - 3)] + '...'

            if self.suggest_max_rows:
                rows = self.squeeze_keyboard(rows)
                rows = rows[:self.suggest_max_rows]

            result['keyboard'] = {
                'one_time': True,
                'buttons': rows,
            }
        return result

    def squeeze_keyboard(self, rows):
        """ Shorten some buttons so that all buttons fit into the screen """
        for _ in range(100):
            if len(rows) <= self.suggest_max_rows:
                break
            # estimate free space in each row
            potentials = [
                sum([len(button['action']['label']) + self.suggest_margin * 2 for button in row])
                for row in rows
            ]
            # find two neighbor rows with most total free space
            best_pot = 1000
            best_i = 0
            for i in range(1, len(rows)):
                pot = potentials[i - 1] + potentials[i]
                if pot <= best_pot and len(rows[i-1]) + len(rows[i]) <= self.suggest_max_cols:
                    best_pot, best_i = pot, i
            if best_i == 0:
                break
            # calculate button sizes if the rows are merged
            to_reduce = best_pot - self.suggest_screen
            new_buttons = [copy.deepcopy(b) for row in rows[best_i - 1:best_i + 1] for b in row]
            sizes = [len(b['action']['label']) for b in new_buttons]
            while to_reduce > 0 and max(sizes) > 3:
                new_sizes = []
                maxsize = max(sizes)
                for s in sizes:
                    if s == maxsize and to_reduce:
                        s -= 1
                        to_reduce -= 1
                    new_sizes.append(s)
                sizes = new_sizes
            # actually, reduce the buttons
            for new_size, b in zip(sizes, new_buttons):
                n = len(b['action']['label'])
                if n > new_size:
                    b['action']['label'] = b['action']['label'][:new_size - 3] + '...'
            # update the rows
            rows = rows[:best_i - 1] + [new_buttons] + rows[best_i + 1:]
        return rows

    def serialize_context(self, context: Context, data=None, **kwargs) -> Optional[SerializedMessage]:
        serializable_message = {'message': context.raw_message and context.raw_message.to_json()}
        return super(VkAdapter, self).serialize_context(context=context, data=serializable_message, **kwargs)
