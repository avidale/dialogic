"""
Automaton dialog manager is based on several concepts:
- phrase: a template, based on which the current response can be generated
- intent: a class with which user input (not only text!) can be matched
- state: a node that defines current phrase and allowed next transitions
- transition: pair (intent, next state, [prefix phrase, condition])

"""
import attr
import copy
import logging

from collections import Counter, defaultdict, OrderedDict
from collections.abc import Mapping
from typing import Dict, Optional, Tuple

from tgalice.dialog import Context, Response
from tgalice.dialog.phrase import Phrase
from tgalice.nlu.matchers import make_matcher, RegexMatcher
from tgalice.utils.configuration import load_config

from tgalice.dialog_manager.base import CascadableDialogManager


logger = logging.getLogger(__name__)

ANY_STATE = 'universal_state'


class State:
    def __init__(self, name, phrase, additional_suggests=None, restore_prev_state=False):
        self.name = name
        self.phrase = phrase
        self.additional_suggests = additional_suggests or []
        self.restore_prev_state = restore_prev_state  # useful for intents like contextual help
        # todo: choose the phrase depending on the prev state (or some other condition)


class Intent:
    def __init__(self, name, regex=None, examples=None, threshold=None):
        self.name = name
        self.regex = regex
        self.examples = examples or []
        self.threshold = threshold  # custom threshold for matcher

    def __repr__(self):
        return 'Intent({})'.format(self.name)


class Transition:
    def __init__(self, name, intent, prev_state, next_state, priority=1):
        # todo: add different transition conditions, beside intents: e.g. callback_data or custom_filter
        self.name = name
        self.intent = intent
        self.prev_state = prev_state
        self.next_state = next_state
        self.priority = priority

    def __repr__(self):
        return 'Transition({}, {}, {}, {})'.format(self.name, self.intent, self.prev_state, self.next_state)


@attr.s
class FSAConfigOptions:
    name: str = attr.ib(default='default_automaton')
    initial_state: str = attr.ib(default=None)
    state_on_new_session: str = attr.ib(default=None)

    @classmethod
    def from_dict(cls, data=None):
        if isinstance(data, cls):
            return data
        return cls(**(data or {}))


@attr.s
class FSAConfig:
    states = attr.ib(factory=dict)
    intents = attr.ib(factory=dict)
    transitions = attr.ib(factory=dict)
    phrases = attr.ib(factory=dict)
    options = attr.ib(converter=FSAConfigOptions.from_dict, factory=FSAConfigOptions.from_dict)


class AutomatonDialogManager(CascadableDialogManager):
    def __init__(self, config, matcher='exact', match_score_first=False, **kwargs):
        super(AutomatonDialogManager, self).__init__(**kwargs)
        if isinstance(matcher, str):
            matcher = make_matcher(matcher)
        elif isinstance(matcher, Mapping):
            matcher = make_matcher(**matcher)
        self.matcher = matcher
        self.regex_matcher = RegexMatcher()
        self.match_score_first = match_score_first

        if not isinstance(config, FSAConfig):
            config = FSAConfig(**load_config(config))
        self._cfg = config
        if not self._cfg.states:
            raise ValueError('The "states" config property cannot be empty.')

        self.phrases: OrderedDict[str, Phrase] = OrderedDict()
        self.intents: OrderedDict[str, Intent] = OrderedDict()
        self.states: OrderedDict[str, State] = OrderedDict()
        self.transitions: OrderedDict[str, Transition] = OrderedDict()
        self.intent2transition = defaultdict(list)

        self.universal_state = self.add_state(name=ANY_STATE, phrase=None)
        # todo: make sure this state is never the destination

        for phrase_name, kw in self._cfg.phrases.items():
            self.add_phrase(name=phrase_name, **kw)
        for intent_name, kw in self._cfg.intents.items():
            self.add_intent(name=intent_name, **kw)
        for state_name, kw in self._cfg.states.items():
            self.add_state(name=state_name, **kw)
        for transition_name, kw in self._cfg.transitions.items():
            self.add_transition(name=transition_name, **kw)

        # the first state is Universal and should be skipped
        self.initial_state = self._cfg.options.initial_state or list(self.states.keys())[1]
        self.state_on_new_session = self._cfg.options.state_on_new_session or self.initial_state
        self.name = self._cfg.options.name

        self.validate()

        self.compile_matchers()

    @property
    def _collections(self):
        return {
            'intent': self.intents,
            'phrase': self.phrases,
            'transition': self.transitions,
            'state': self.states,
        }

    def _check_name(self, entity_type, name, kwargs):
        collection = self._collections[entity_type]
        if name is None:
            if 'label' in kwargs:
                name = kwargs['label']
                del kwargs['label']
            else:
                name = '{}__{}'.format(entity_type, len(collection))
        assert name not in collection
        return name

    def add_state(self, name=None, **kwargs) -> State:
        kwargs = copy.deepcopy(kwargs)
        name = self._check_name('state', name, kwargs)
        if 'q' in kwargs:
            intent = self.add_intent(name=name, examples=kwargs['q'])
            del kwargs['q']
            self.add_transition(
                intent=intent.name,
                prev_state=ANY_STATE,
                next_state=name,
            )
        if 'a' in kwargs:
            phrase = self.add_phrase(name=name, text=kwargs['a'])
            del kwargs['a']
            kwargs['phrase'] = phrase.name
        if 'next' in kwargs:
            for transition_args in kwargs['next']:
                if 'label' in transition_args:
                    if 'intent' in transition_args:
                        new_intent_name = transition_args['intent']
                    else:
                        examples = transition_args.get('examples', [])
                        if 'suggest' in transition_args:
                            examples.append(transition_args['suggest'])
                        new_intent = self.add_intent(
                            regex=transition_args.get('regex'),
                            examples=examples,
                        )
                        new_intent_name = new_intent.name
                    self.add_transition(
                        intent=new_intent_name,
                        prev_state=name,
                        next_state=transition_args['label'],
                    )
                if 'suggest' in transition_args:
                    if 'additional_suggests' not in kwargs:
                        kwargs['additional_suggests'] = []
                    kwargs['additional_suggests'].append(transition_args['suggest'])
            del kwargs['next']
        if 'default_next' in kwargs:
            self.add_transition(
                intent=None,  # todo: add special tags to transitions-without-intents
                prev_state=name,
                next_state=kwargs['default_next'],
            )
            del kwargs['default_next']

        state = State(name=name, **kwargs)
        self.states[name] = state
        return state

    def add_phrase(self, name=None, **kwargs) -> Phrase:
        kwargs = copy.deepcopy(kwargs)
        name = self._check_name('phrase', name, kwargs)
        phrase = Phrase(name=name, **kwargs)
        self.phrases[name] = phrase
        return phrase

    def add_intent(self, name=None, **kwargs) -> Intent:
        kwargs = copy.deepcopy(kwargs)
        name = self._check_name('intent', name, kwargs)
        intent = Intent(name=name, **kwargs)
        self.intents[name] = intent
        return intent

    def add_transition(self, name=None, **kwargs) -> Transition:
        kwargs = copy.deepcopy(kwargs)
        name = self._check_name('transition', name, kwargs)
        transition = Transition(name=name, **kwargs)
        self.transitions[name] = transition
        self.intent2transition[transition.intent].append(transition.name)
        return transition

    def validate(self, silent=False):
        errors = []
        for transition_name, transition in self.transitions.items():
            if transition.prev_state not in self.states:
                errors.append('State {} not found'.format(transition.prev_state))
            if transition.next_state not in self.states:
                errors.append('State {} not found'.format(transition.next_state))
            if transition.intent not in self.intents and transition.intent is not None:
                errors.append('Intent {} not found'.format(transition.intent))
        if errors and not silent:
            raise ValueError('\n'.join(['Some transitions were invalid. Errors:'] + errors))
        return errors

    def compile_matchers(self):
        texts = []
        labels = []
        for intent_name, intent in self.intents.items():
            for example in intent.examples:
                texts.append(example)
                labels.append(intent.name)
            if intent.threshold:
                self.matcher.thresholds[intent_name] = intent.threshold
        self.matcher.fit(texts, labels)

        texts = []
        labels = []
        for intent_name, intent in self.intents.items():
            if not intent.regex:
                continue
            regex = intent.regex
            if not isinstance(regex, list):
                regex = [regex]
            for example in regex:
                texts.append(example)
                labels.append(intent.name)
        self.regex_matcher.fit(texts, labels)

    def extract_prev_state(self, context: Context) -> Optional[State]:
        state_name = context.user_object.get('automaton', {}).get(self.name, {}).get('state_name')
        if state_name:
            return self.states[state_name]

    def try_to_respond(self, ctx: Context) -> Optional[Response]:
        prev_state = self.extract_prev_state(ctx)
        logger.debug('Prev state is ', prev_state)
        if prev_state is None:
            new_state_name, updated_user_object = self.initialize(ctx)
        else:
            new_state_name, updated_user_object = self.do_transition(prev_state, ctx)
        logger.debug('New state is ', new_state_name)
        if new_state_name is None:
            # todo: maybe do some default action
            pass
        if new_state_name is not None:
            new_state = self.states[new_state_name]
            phrase = self.phrases[new_state.phrase]
            response = phrase.render(additional_suggests=new_state.additional_suggests)
            if prev_state and new_state.restore_prev_state:
                self.remember_new_state(prev_state.name, updated_user_object)
            response.updated_user_object = updated_user_object
            return response
        return None

    def initialize(self, context) -> Tuple[str, dict]:
        user_object = context.user_object
        self.remember_new_state(self.initial_state, user_object)
        return self.initial_state, user_object

    def get_intent_scores(self, context: Context) -> Counter:
        scores = self.matcher.aggregate_scores(context.message_text)
        scores.update(self.regex_matcher.aggregate_scores(context.message_text))
        if context.yandex and context.yandex.request.nlu:
            for intent in context.yandex.request.nlu.intents:
                scores[intent] = 1
        return scores

    def do_transition(self, prev_state: State, context: Context) -> Tuple[Optional[str], Optional[dict]]:
        if context.message_text:
            scores = self.get_intent_scores(context=context)
            next_state_name, match_score = None, None
            # todo: реализовать сортировку в любом порядке: скор, номер перехода, приоритет
            for intent_name, score in scores.most_common():
                next_state_name = self.find_transition_by_intent(intent_name, prev_state)
                logger.debug('valid transition to {} with intent {}'.format(next_state_name, intent_name))
            if next_state_name is None:
                # the transitions-without-text have lower priority than any text (not sure)
                next_state_name = self.find_transition_by_intent(None, prev_state)
            if next_state_name is None:
                return None, None
            user_object = context.user_object
            self.remember_new_state(next_state_name, user_object)
            return next_state_name, user_object
        elif context.session_is_new():
            next_state_name = self.state_on_new_session
            user_object = context.user_object
            self.remember_new_state(next_state_name, user_object)
            return next_state_name, user_object
        else:
            # todo: find a convenient way to match non-text inputs
            return None, None

    def remember_new_state(self, new_state_name: str, user_object: Optional[Mapping]):
        if user_object is None:
            user_object = {}
        if 'automaton' not in user_object:
            user_object['automaton'] = {}
        if self.name not in user_object['automaton']:
            user_object['automaton'][self.name] = {}
        user_object['automaton'][self.name]['state_name'] = new_state_name
        return user_object

    def find_transition_by_intent(self, intent, prev_state: State):
        for transition_name in self.intent2transition[intent]:
            transition = self.transitions[transition_name]
            if transition.prev_state != prev_state.name and transition.prev_state != ANY_STATE:
                continue
            return transition.next_state
