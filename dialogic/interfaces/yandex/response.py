"""
This package implements Yandex.Dialogs response protocol.
The official documentation is available at
https://yandex.ru/dev/dialogs/alice/doc/protocol-docpage/#response
"""

import attr
import copy

from typing import Union, Dict, List, Optional
from dialogic.utils.serialization import Serializeable, list_converter


class CARD_TYPES:
    BIG_IMAGE = 'BigImage'
    ITEMS_LIST = 'ItemsList'
    IMAGE_GALLERY = 'ImageGallery'


@attr.s
class Button(Serializeable):
    title: str = attr.ib()
    payload = attr.ib()
    url: str = attr.ib()
    hide: bool = attr.ib()


@attr.s
class Card(Serializeable):
    type: str = attr.ib()


@attr.s
class CardButton(Serializeable):
    text: str = attr.ib(default=None)
    url: str = attr.ib(default=None)
    payload = attr.ib(default=None)


@attr.s
class BigImage(Card):
    type: str = attr.ib(default=CARD_TYPES.BIG_IMAGE, init=False)
    image_id: str = attr.ib()
    title: str = attr.ib(default=None)
    description: str = attr.ib(default=None)
    button: CardButton = attr.ib(default=None, converter=CardButton.from_dict)


@attr.s
class ItemsListHeader(Serializeable):
    text: str = attr.ib()


@attr.s
class ItemsListFooter(Serializeable):
    text: str = attr.ib()
    button: Optional[CardButton] = attr.ib(default=None, converter=CardButton.from_dict)


@attr.s
class ItemsListItem(Serializeable):
    image_id: str = attr.ib(default=None)
    title: str = attr.ib(default=None)
    description: str = attr.ib(default=None)
    button: CardButton = attr.ib(default=None, converter=CardButton.from_dict)


@attr.s
class ItemsList(Card):
    type: str = attr.ib(default=CARD_TYPES.ITEMS_LIST, init=False)
    header: Optional[ItemsListHeader] = attr.ib(converter=ItemsListHeader.from_dict, default=None)
    items: List[ItemsListItem] = attr.ib(converter=list_converter(ItemsListItem), factory=list)
    footer: Optional[ItemsListFooter] = attr.ib(converter=ItemsListFooter.from_dict, default=None)


@attr.s
class ImageGalleryItem(Serializeable):
    image_id: str = attr.ib(default=None)
    title: str = attr.ib(default=None)


@attr.s
class ImageGallery(Card):
    type: str = attr.ib(default=CARD_TYPES.IMAGE_GALLERY, init=False)
    items: List[ImageGalleryItem] = attr.ib(converter=list_converter(ImageGalleryItem), factory=list)


@attr.s
class ShowItemMeta(Serializeable):
    content_id: Optional[str] = attr.ib(default=None)
    title: Optional[str] = attr.ib(default=None)
    title_tts: Optional[str] = attr.ib(default=None)
    publication_date: Optional[str] = attr.ib(default=None)  # like "2020-12-03T10:39:32.195044179Z"
    expiration_date: Optional[str] = attr.ib(default=None)


def card_converter(data):
    if not data:
        return None
    if isinstance(data, Card):
        return data
    new_data = copy.deepcopy(data)
    card_type = new_data['type']
    del new_data['type']

    if card_type == CARD_TYPES.BIG_IMAGE:
        return BigImage.from_dict(new_data)
    if card_type == CARD_TYPES.ITEMS_LIST:
        return ItemsList.from_dict(new_data)
    if card_type == CARD_TYPES.IMAGE_GALLERY:
        return ImageGallery.from_dict(new_data)


@attr.s
class Response(Serializeable):
    text: str = attr.ib()
    tts: str = attr.ib(default=None)
    buttons: List[Button] = attr.ib(converter=list_converter(Button), factory=list)
    card: Optional[Union[BigImage, ItemsList, ImageGallery]] = attr.ib(converter=card_converter, default=None)
    end_session: bool = attr.ib(default=False)
    show_item_meta: Optional[ShowItemMeta] = attr.ib(default=None, converter=ShowItemMeta.from_dict)
    directives: Optional[Dict] = attr.ib(default=None)


@attr.s
class YandexResponse(Serializeable):
    response: Response = attr.ib(converter=Response.from_dict)
    session_state: Optional[Dict] = attr.ib(default=None)
    user_state_update: Optional[Dict] = attr.ib(default=None)
    session = attr.ib(default=None)
    version: str = attr.ib(default='1.0')
