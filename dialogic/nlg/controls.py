import json
import sys

from collections.abc import Iterable, Mapping
from collections import OrderedDict


def make_button(button=None, text=None, url=None, payload=None):
    if isinstance(button, GalleryButton):
        return button
    elif isinstance(button, Mapping):
        return GalleryButton(**button)
    elif text is not None or url is not None or payload is not None:
        return GalleryButton(text=text, url=url, payload=payload)
    else:
        return None


class Button:
    def __init__(self, title=None, payload=None, url=None, hide=True):
        # todo: write getters and setters with validation
        self.title = title
        if self.title is None:
            raise ValueError('Button title cannot be empty')
        else:
            assert len(self.title) <= 64, 'Button title cannot be longer than 64 symbols'
        self.payload = payload
        if self.payload is not None:
            assert sys.getsizeof(json.dumps(self.payload)) <= 4096, 'Size of button payload cannot exceed 4096 bytes'
        self.url = url
        if self.url is not None:
            assert sys.getsizeof(self.url) <= 1024, 'Size of button URL cannot exceed 1024 bytes'
        self.hide = bool(hide)

    def to_dict(self):
        result = OrderedDict()
        if self.title is not None:
            result['title'] = self.title
        if self.payload is not None:
            result['payload'] = self.payload
        if self.url is not None:
            result['url'] = self.url
        result['hide'] = self.hide
        return result


class BigImage:
    def __init__(self, image_id=None, title=None, description=None,
                 button=None, button_text=None, button_url=None, button_payload=None):
        self.image_id = image_id
        self.title = title
        self.description = description
        if self.description is not None:
            assert len(self.description) <= 256, 'Big Image description cannot be longer than 256 symbols'
        self.button = make_button(button, button_text, button_url, button_payload)

    def to_dict(self):
        result = OrderedDict()
        result['type'] = 'BigImage'
        result['image_id'] = self.image_id
        if self.title is not None:
            result['title'] = self.title
        if self.description is not None:
            result['description'] = self.description
        if self.button is not None:
            result['button'] = self.button.to_dict()
        return result


class GalleryButton:
    def __init__(self, text=None, payload=None, url=None):
        # todo: write getters and setters with validation
        self.text = text
        if self.text is not None:
            assert len(self.text) <= 64, 'Button title cannot be longer than 64 symbols'
        self.payload = payload
        if self.payload is not None:
            assert sys.getsizeof(json.dumps(self.payload)) <= 4096, 'Size of button payload cannot exceed 4096 bytes'
        self.url = url
        if self.url is not None:
            assert sys.getsizeof(self.url) <= 1024, 'Size of button URL cannot exceed 1024 bytes'

    def to_dict(self):
        result = OrderedDict()
        if self.text is not None:
            result['text'] = self.text
        if self.payload is not None:
            result['payload'] = self.payload
        if self.url is not None:
            result['url'] = self.url
        return result


class GalleryItem:
    def __init__(self, image_id=None, title=None, description=None,
                 button=None, button_text=None, button_url=None, button_payload=None):
        self.image_id = image_id
        self.title = title
        self.description = description
        if self.description is not None:
            assert len(self.description) <= 256, 'Gallery item description cannot be longer than 256 symbols'
        self.button = make_button(button, button_text, button_url, button_payload)

    def to_dict(self):
        result = OrderedDict()
        if self.image_id is not None:
            result['image_id'] = self.image_id
        if self.title is not None:
            result['title'] = self.title
        if self.description is not None:
            result['description'] = self.description
        if self.button is not None:
            result['button'] = self.button.to_dict()
        return result


class GalleryFooter:
    def __init__(self, text=None,
                 button=None, button_text=None, button_url=None, button_payload=None):
        self.text = text
        if self.text is not None:
            assert len(self.text) <= 64, 'Gallery footer text cannot be longer than 64 symbols'
        self.button = make_button(button, button_text, button_url, button_payload)

    def to_dict(self):
        result = OrderedDict()
        if self.text is not None:
            result['text'] = self.text
        if self.button is not None:
            result['button'] = self.button.to_dict()
        return result


class Gallery:
    def __init__(self, title=None, items=None, footer=None):
        self.title = title
        if self.title is not None:
            assert len(self.title) <= 64, 'Gallery header text cannot be longer than 64 symbols'
        if not isinstance(items, Iterable):
            raise ValueError('Gallery items should be an Iterable, got {}'.format(type(items)))
        if items is None:
            items = []
        if len(items) < 1 or len(items) > 5:
            raise ValueError('Gallery should contain 1-5 items, got {}'.format(len(items)))
        self.items = items
        if footer is not None:
            assert isinstance(footer, GalleryFooter)
            # todo: make footer create-able from config
        self.footer = footer

    def to_dict(self):
        result = OrderedDict()
        result['type'] = 'ItemsList'
        if self.title is not None:
            result['header'] = {'text': self.title}
        result['items'] = [item.to_dict() for item in self.items]
        if self.footer is not None:
            result['footer'] = self.footer.to_dict()
        return result
