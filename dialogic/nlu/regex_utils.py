import re
from typing import Dict

try:
    import regex
except ImportError:
    regex = None

regex_or_re = regex or re


def drop_none(d):
    return {k: v for k, v in d.items() if v is not None}


def match_forms(text: str, intents: dict) -> Dict[str, Dict]:
    forms = {}
    for intent_name, intent_value in intents.items():
        if 'regexp' in intent_value:
            expressions = intent_value['regexp']
            if isinstance(expressions, str):
                expressions = [expressions]
            for exp in expressions:
                match = regex_or_re.match(exp, text)
                if match:
                    forms[intent_name] = drop_none(match.groupdict())
                    break
    return forms
