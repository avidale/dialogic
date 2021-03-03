import logging
import time
import yaml
from typing import Union, Type, Tuple, Dict

from ..interfaces.yandex import extract_yandex_forms
from ..nlu.regex_utils import match_forms
from dialogic.cascade import DialogTurn
from dialogic.dialog import Context, Response
from dialogic.dialog_manager import CascadableDialogManager
from dialogic.nlu.basic_nlu import fast_normalize
from dialogic.nlu.matchers import TFIDFMatcher, TextNormalization, make_matcher_with_regex

logger = logging.getLogger(__name__)


class TurnDialogManager(CascadableDialogManager):
    def __init__(
            self,
            cascade,
            intents_file=None,
            turn_cls: Type[DialogTurn] = DialogTurn,
            **kwargs
    ):
        super(TurnDialogManager, self).__init__(**kwargs)

        self.cascade = cascade
        self.turn_cls: Type[DialogTurn] = turn_cls

        self.intents_file = intents_file
        self.intents = {}
        self.intent_matcher = None
        if intents_file:
            self.load_intents(intents_file=intents_file)

    def load_intents(self, intents_file=None):
        with open(intents_file, 'r', encoding='utf-8') as f:
            self.intents = yaml.safe_load(f)

        self.intent_matcher = make_matcher_with_regex(
            base_matcher=TFIDFMatcher(text_normalization=TextNormalization.FAST_LEMMATIZE),
            intents=self.intents,
        )

    def try_to_respond(self, ctx: Context) -> Union[Response, None]:
        t = time.time()
        self.preprocess_context(ctx=ctx)
        text, intents, forms = self.nlu(ctx=ctx)
        turn = self.turn_cls(
            ctx=ctx,
            text=text,
            intents=intents,
            forms=forms,
            user_object=ctx.user_object or {},
        )
        self.preprocess_turn(turn=turn)
        handler_name = self.cascade(turn)
        logger.debug(f"Final handler: {handler_name}")
        response = turn.make_response()
        self.postprocess_response(response=response, turn=turn)
        logger.debug(f'DM response took {time.time() - t} seconds')
        return response

    def nlu(self, ctx: Context) -> Tuple[str, Dict[str, float], Dict[str, Dict]]:
        text = fast_normalize(ctx.message_text or '')
        if self.intent_matcher:
            intents = self.intent_matcher.aggregate_scores(text)
        else:
            intents = {}
        forms = match_forms(text=text, intents=self.intents or {})
        if ctx.yandex:
            ya_forms = extract_yandex_forms(ctx.yandex)
            forms.update(ya_forms)
            for intent_name in ya_forms:
                intents[intent_name] = 1
        return text, intents, forms

    def preprocess_context(self, ctx: Context):
        if not ctx.user_object:
            ctx.add_user_object({})
        if ctx.session_is_new():
            if 'stage' in ctx.user_object:
                del ctx.user_object['stage']
            ctx.user_object['sessions_count'] = ctx.user_object.get('sessions_count', 0) + 1

    def preprocess_turn(self, turn: DialogTurn):
        pass

    def postprocess_response(self, response: Response, turn):
        pass
