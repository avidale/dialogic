import re
import random

_RANDOM: bool = True


def random_on():
    global _RANDOM
    _RANDOM = True


def random_off():
    global _RANDOM
    _RANDOM = False


def sample(pattern, rnd=None, sep='|', drop_proba=0.5):
    """ Sample various texts from patterns such as '{Okay|well}{ dude}*, when should we {begin|start}?'
    Group of options are enclosed by '{}' brackets and separated by `sep`. Nested groups are not supported.
    The groups marked by '*' star are omitted with probability `drop_proba`.
    If `rnd` is False, the first option is always returned, which may simplify testing or debugging.
    """
    if rnd is None:
        rnd = _RANDOM

    def f(x):
        options = x.group(1).split(sep)
        if not options:
            return ''
        if not rnd:
            return options[0]
        if drop_proba == 1:
            return ''
        elif drop_proba == 0:
            pass
        elif x.group().endswith('*') and random.random() > drop_proba:
            return ''
        return random.choice(options)

    return re.sub('{([^}]*?)}\\*?', f, pattern)
