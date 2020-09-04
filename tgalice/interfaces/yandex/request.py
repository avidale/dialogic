"""
This package implements Yandex.Dialogs request protocol.
The official documentation is available at
https://yandex.ru/dev/dialogs/alice/doc/protocol-docpage/#request
"""

import attr
from typing import Dict, List, Optional
from tgalice.utils.serialization import Serializeable, list_converter, dict_converter


class ENTITY_TYPES:
    YANDEX_GEO = 'YANDEX.GEO'
    YANDEX_FIO = 'YANDEX.FIO'
    YANDEX_NUMBER = 'YANDEX.NUMBER'
    YANDEX_DATETIME = 'YANDEX.DATETIME'


@attr.s
class Meta(Serializeable):
    locale: str = attr.ib()
    timezone: str = attr.ib()
    client_id: str = attr.ib()
    interfaces: dict = attr.ib(factory=dict)

    @property
    def has_screen(self) -> bool:
        return self.interfaces and 'screen' in self.interfaces

    @property
    def has_account_linking(self) -> bool:
        return self.interfaces and 'account_linking' in self.interfaces


@attr.s
class Span(Serializeable):
    start: int = attr.ib()
    end: int = attr.ib()


@attr.s
class Entity(Serializeable):
    type: str = attr.ib()  # may be one of ENTITY_TYPES, but not only
    tokens: Span = attr.ib(converter=Span.from_dict)
    value = attr.ib()


@attr.s
class Slot(Serializeable):
    type: str = attr.ib()
    tokens: Optional[Span] = attr.ib(converter=Span.from_dict, default=None)
    value = attr.ib(default=None)


@attr.s
class Intent(Serializeable):
    slots: Dict[str, Slot] = attr.ib(converter=dict_converter(Slot))

    def get_form(self) -> Dict[str, str]:
        return {
            slot_name: slot.value
            for slot_name, slot in self.slots.items()
        }


@attr.s
class NLU(Serializeable):
    tokens: List[str] = attr.ib(factory=list)
    entities: List[Entity] = attr.ib(converter=list_converter(Entity), factory=list)
    intents: Dict[str, Intent] = attr.ib(converter=dict_converter(Intent), factory=dict)

    def get_forms(self) -> Dict[str, Dict[str, str]]:
        return {
            intent_name: intent.get_form()
            for intent_name, intent in self.intents.items()
        }


@attr.s
class Request(Serializeable):
    command: str = attr.ib(default=None)
    original_utterance: str = attr.ib(default=None)
    type: str = attr.ib(default=None)
    markup = attr.ib(factory=dict)
    payload = attr.ib(factory=dict)
    nlu: Optional[NLU] = attr.ib(converter=NLU.from_dict, default=None)


class User:
    user_id: str = attr.ib(default=None)
    access_token: str = attr.ib(default=None)


class Application:
    application_id: str = attr.ib(default=None)


@attr.s
class Session(Serializeable):
    message_id: int = attr.ib()
    session_id: str = attr.ib()
    skill_id: str = attr.ib()
    # user_id is deprecated, use application.application_id or user.user_id instead
    user_id: str = attr.ib()
    user: Optional[User] = attr.ib(default=None)
    application: Optional[Application] = attr.ib(default=None)
    new: bool = attr.ib(default=False)


@attr.s
class State(Serializeable):
    session: Optional[Dict] = attr.ib(default=None)
    user: Optional[Dict] = attr.ib(default=None)


@attr.s
class YandexRequest(Serializeable):
    meta: Meta = attr.ib(converter=Meta.from_dict)
    request: Request = attr.ib(converter=Request.from_dict)
    session: Optional[Session] = attr.ib(converter=Session.from_dict)
    new: bool = attr.ib(default=False)
    version: str = attr.ib(default='1.0')
    state: Optional[State] = attr.ib(converter=State.from_dict, default=None)
