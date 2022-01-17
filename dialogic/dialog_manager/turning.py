import logging
import time
import yaml
from typing import Union, Type, Tuple, Dict

from ..nlu.regex_expander import load_intents_with_replacement
from ..interfaces.yandex import extract_yandex_forms
from ..nlu.regex_utils import match_forms
from dialogic.cascade import DialogTurn
from dialogic.dialog import Context, Response
from dialogic.dialog_manager import CascadableDialogManager
from dialogic.nlu import basic_nlu
from dialogic.nlu.basic_nlu import fast_normalize
from dialogic.nlu.matchers import TFIDFMatcher, TextNormalization, make_matcher_with_regex, AggregationMatcher

logger = logging.getLogger(__name__)


class TurnDialogManager(CascadableDialogManager):
    TURN_CLS = DialogTurn

    def __init__(
            self,
            cascade,
            intents_file=None,
            expressions_file=None,
            matcher_threshold=0.8,
            add_basic_nlu=True,
            turn_cls: Type[DialogTurn] = None,
            reset_stage=True,
            **kwargs
    ):
        super(TurnDialogManager, self).__init__(**kwargs)

        self.cascade = cascade
        self.turn_cls: Type[DialogTurn] = turn_cls or self.TURN_CLS

        self.intents_file = intents_file
        self.expressions_file = expressions_file
        self.intents = {}
        self.intent_matcher: AggregationMatcher = None
        self.matcher_threshold = matcher_threshold
        self.add_basic_nlu = add_basic_nlu
        self.reset_stage = reset_stage

        if intents_file:
            self.load_intents(intents_file=intents_file)

    def load_intents(self, intents_file=None):
        if self.expressions_file and self.intents_file:
            self.intents = load_intents_with_replacement(
                intents_fn='texts/intents.yaml',
                expressions_fn='texts/expressions.yaml',
            )
        elif self.intents_file:
            with open(intents_file, 'r', encoding='utf-8') as f:
                self.intents = yaml.safe_load(f)
        else:
            return

        self.intent_matcher = make_matcher_with_regex(
            base_matcher=TFIDFMatcher(
                text_normalization=TextNormalization.FAST_LEMMATIZE, threshold=self.matcher_threshold
            ),
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
        response.handler = handler_name
        self.postprocess_response(response=response, turn=turn)
        logger.debug(f'DM response took {time.time() - t} seconds')
        return response

    def normalize_text(self, ctx: Context):
        text = fast_normalize(ctx.message_text or '')
        return text

    def nlu(self, ctx: Context) -> Tuple[str, Dict[str, float], Dict[str, Dict]]:
        text = self.normalize_text(ctx=ctx)
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

        if self.add_basic_nlu:
            if basic_nlu.like_help(ctx.message_text):
                intents['help'] = max(intents.get('help', 0), 0.9)
            if basic_nlu.like_yes(ctx.message_text):
                intents['yes'] = max(intents.get('yes', 0), 0.9)
            if basic_nlu.like_no(ctx.message_text):
                intents['no'] = max(intents.get('no', 0), 0.9)

        return text, intents, forms

    def preprocess_context(self, ctx: Context):
        if not ctx.user_object:
            ctx.add_user_object({})
        if ctx.session_is_new():
            if 'stage' in ctx.user_object and self.reset_stage:
                del ctx.user_object['stage']
            ctx.user_object['sessions_count'] = ctx.user_object.get('sessions_count', 0) + 1

    def preprocess_turn(self, turn: DialogTurn):
        pass

    def postprocess_response(self, response: Response, turn):
        pass
