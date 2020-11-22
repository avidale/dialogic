"""
This module allows creating reusable parts of regular expressions.
It might be useful for matching intents or extracting slots.
The resulting language is not as powerful as grammars, but close to it.

The example below consists of two data files and a code file:
The file `expressions.yaml`:
```
NUMBER: '[0-9]+'
_NUMBER_GROUP: '(number )?(?P<id>{{NUMBER}})'
```
The file `intents.yaml`:
```
choose:
    regex: '((choose|take|set) )?{{_NUMBER_GROUP}}'
```
The file `code.py`:
```
intents = load_intents_with_replacement('intents.yaml', 'expressions.yaml')
matcher = make_matcher_with_regex(TFIDFMatcher(), intents=intents)
print(matcher.match('take number 10'))
"""

import re
import yaml


def _patch(text, expressions):
    def sub_maker(match):
        return '({})'.format(expressions[match.group(1)])
    return re.sub('{{\\s*([a-zA-Z_]+)\\s*}}', sub_maker, text)


def load_expressions(filename):
    with open(filename, encoding='utf-8') as f:
        expressions = yaml.safe_load(f)
    for k in list(expressions.keys()):
        expressions[k] = _patch(expressions[k], expressions)
    return expressions


def load_intents_with_replacement(intents_fn, expressions_fn):
    expressions = load_expressions(expressions_fn)
    with open(intents_fn, encoding='utf-8') as f:
        intents = yaml.safe_load(f)
    for v in intents.values():
        if 'regexp' in v:
            if isinstance(v['regexp'], list):
                v['regexp'] = [_patch(e, expressions) for e in v['regexp']]
            elif isinstance(v['regexp'], str):
                v['regexp'] = _patch(v['regexp'], expressions)
    return intents
