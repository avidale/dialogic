import attr
import logging

from tgalice.dialog import Context, Response
from tgalice.utils.content_manager import YandexImageAPI
from tgalice.nlg.controls import Gallery as VisualGallery, BigImage
from typing import Dict, List, Optional, Union, Tuple

logger = logging.getLogger(__name__)


FORM_TYPE = Dict[str, Dict]


@attr.s
class DialogTurn:
    """ DialogTurn is a single-variable wrapper for both context and response """
    ctx: Context = attr.ib()
    # These properties are extracted from context:
    text: str = attr.ib()
    intents: Dict = attr.ib(factory=dict)
    forms: Dict[str, Dict] = attr.ib(factory=dict)
    # These properties will be put into response:
    response_text: str = attr.ib(default='')
    response: Optional[Response] = attr.ib(default=None)
    user_object = attr.ib(factory=dict)
    suggests: List = attr.ib(factory=list)
    commands: List = attr.ib(factory=list)
    card: Optional[Union[VisualGallery, BigImage]] = attr.ib(default=None)
    image_url: Optional[str] = attr.ib(default=None)
    # These properties are helpers
    image_manager: Optional[YandexImageAPI] = attr.ib(default=None)
    can_change_topic: bool = attr.ib(default=False)

    _STAGE = 'stage'
    _AGENDA = 'agenda'
    _AGENDA_FORMS = 'agenda_forms'

    @property
    def old_user_object(self):
        return self.ctx.user_object

    @property
    def is_complete(self):
        return bool(self.response_text) or bool(self.response)

    @property
    def stage(self) -> Optional[str]:
        return self.old_user_object.get(self._STAGE)

    @property
    def next_stage(self) -> Optional[str]:
        return self.user_object.get(self._STAGE)

    @stage.setter
    def stage(self, value):
        self.user_object[self._STAGE] = value

    def release_control(self):
        self.can_change_topic = True

    def take_control(self):
        self.can_change_topic = False

    @property
    def can_take_control(self) -> bool:
        return self.can_change_topic and not self.next_stage

    @property
    def agenda(self) -> List[str]:
        """ The stack of postprocessors waiting to be triggered """
        return self.user_object.get(self._AGENDA, [])

    @property
    def agenda_forms(self) -> FORM_TYPE:
        """ The forms to be fed into postprocessors """
        return self.user_object.get(self._AGENDA_FORMS, {})

    def add_agenda(self, postprocessor_name: str, form: Dict = None) -> bool:
        if not self.agenda:
            self.user_object[self._AGENDA] = []
        if postprocessor_name not in self.agenda:
            # avoiding duplicate agenda and potential cycles
            self.agenda.append(postprocessor_name)
            if form:
                if not self.agenda_forms:
                    self.user_object[self._AGENDA_FORMS] = {}
                self.agenda_forms[postprocessor_name] = form
            return True
        return False

    def pop_agenda(self) -> Tuple[Optional[str], Optional[FORM_TYPE]]:
        if not self.agenda:
            self.clear_agenda()
            return None, None
        key = self.agenda.pop()
        form = self.agenda_forms.get(key)
        if form:
            del self.agenda_forms[key]
        return key, form

    def clear_agenda(self):
        self.user_object[self._AGENDA] = []
        self.user_object[self._AGENDA_FORMS] = {}

    def add_space(self):
        if not self.response_text:
            self.response_text = ''
        else:
            self.response_text += '\n'

    def make_response(self) -> Optional[Response]:
        if self.response:
            return self.response
        if self.response_text:
            r = Response(
                text=None,
                user_object=self.user_object,
                rich_text=self.response_text,
                suggests=self.suggests,
                commands=self.commands,
                image_url=self.image_url,
            )
            if isinstance(self.card, BigImage):
                r.image = self.card
            elif isinstance(self.card, VisualGallery):
                r.gallery = self.card
            return r
