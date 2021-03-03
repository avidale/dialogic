import re

import attr
import logging
import math

from typing import Callable, List, Optional, Dict

from .turn import DialogTurn


logger = logging.getLogger(__name__)

CHECKER_TYPE = Callable[[DialogTurn], bool]
HANDLER_TYPE = Callable[[DialogTurn], bool]
POSTPROCESSOR_TYPE = Callable[[DialogTurn, Optional[Dict]], None]


class Pr:
    EPSILON = 1e-5
    CRITICAL = 100
    STAGE = 10
    STRONG_INTENT = 5  # like 'cancel' for multi-turn scenarios
    WEAK_STAGE = 3  # stages in multi-turn scenarios that can be easily cancelled
    CHECKER = 2
    INTENT_PLUS = 1.1  # local intents, that should compete with each other but not with Yandex intents
    INTENT = 1
    INTENT_MINUS = 0.9
    FAQ = 0.1
    FIND_ANYTHING = 0.05
    BEFORE_FALLBACK = 0.03
    FALLBACK = 0.01


@attr.s
class CascadeItem:
    handler: HANDLER_TYPE = attr.ib()
    priority: float = attr.ib()
    intents: Optional[List[str]] = attr.ib(factory=list)
    stages: Optional[List[str]] = attr.ib(factory=list)
    checker: Optional[CHECKER_TYPE] = attr.ib(default=None)
    regexp: Optional[str] = attr.ib(default=None)


class Cascade:
    def __init__(self):
        self.handlers: List[CascadeItem] = []
        self.postprocessors: Dict[str, POSTPROCESSOR_TYPE] = {}

    def add_handler(
            self,
            priority=None,
            intents=None,
            stages=None,
            checker=None,
            regexp=None,
    ) -> Callable[[HANDLER_TYPE], HANDLER_TYPE]:
        if priority is None:
            if stages:
                priority = Pr.STAGE
            elif intents or regexp:
                priority = Pr.INTENT
            elif checker:
                priority = Pr.CHECKER
            else:
                priority = Pr.FALLBACK

        def wrap(f: HANDLER_TYPE):
            self.handlers.append(CascadeItem(
                handler=f,
                priority=priority,
                intents=intents,
                stages=stages,
                checker=checker,
                regexp=regexp
            ))
            return f
        return wrap

    def __call__(self, turn: DialogTurn) -> Optional[str]:
        if turn.is_complete:
            return None
        candidates = []
        for item in self.handlers:
            # stages are matched strictly
            if item.stages:
                if turn.stage not in item.stages:
                    continue
            # intent scores are matched strictly and then sorted
            intent_score = -math.inf
            if item.intents:
                intent_score = max(turn.intents.get(intent, -math.inf) for intent in item.intents)
            if intent_score < 1 and item.regexp and turn.text is not None:
                if re.match(item.regexp, turn.text):
                    intent_score = 1
            if (item.intents or item.regexp) and intent_score == -math.inf:
                continue
            candidates.append((item.priority, intent_score, item))
        candidates.sort(key=lambda x: x[:2], reverse=True)
        logger.debug('sorted candidates: {}'.format([c[2].handler.__name__ for c in candidates]))

        for candidate in candidates:
            item = candidate[2]
            if item.checker and not item.checker(turn):
                continue
            result = item.handler(turn)
            if turn.is_complete:
                return item.handler.__name__
        return None

    def add_postprocessor(self, name: str, function: POSTPROCESSOR_TYPE):
        self.postprocessors[name] = function

    def get_postprocessor(self, name: str) -> Optional[POSTPROCESSOR_TYPE]:
        return self.postprocessors.get(name)

    def postprocessor(self, function: POSTPROCESSOR_TYPE):
        # this will be used as a decorator
        name = function.__name__
        if name in self.postprocessors:
            logger.warning(
                'registering postprocessor "{}" for a second time'.format(name)
            )
        self.add_postprocessor(name, function)
        return function

    def postprocess(self, turn: DialogTurn):
        if turn.is_complete and turn.can_take_control and turn.agenda:
            key, form = turn.pop_agenda()
            logger.debug('agenda key is: {}'.format(key))
            if not key:
                return
            f = self.get_postprocessor(key)
            if not f:
                return
            if form:
                f(turn, form=form)
            else:
                f(turn)
