import pymorphy2
import re

from functools import lru_cache

PYMORPHY = pymorphy2.MorphAnalyzer()


@lru_cache(maxsize=16384)
def word2lemma(word):
    hypotheses = PYMORPHY.parse(word)
    if len(hypotheses) == 0:
        return word
    return hypotheses[0].normal_form


def fast_normalize(text, lemmatize=False):
    text = re.sub('[^a-zа-яё0-9]+', ' ', text.lower())
    # we consider '-' as a delimiter, because it is often missing in results of ASR
    text = re.sub('\\s+', ' ', text).strip()
    if lemmatize:
        text = ' '.join([word2lemma(w) for w in text.split()])
    text = re.sub('ё', 'е', text)
    return text


def like_help(text):
    text = fast_normalize(text)
    return bool(re.match('^(алиса |яндекс )?(помощь|что ты (умеешь|можешь))$', text))


def like_exit(text):
    text = fast_normalize(text)
    return bool(re.match('^(алиса |яндекс )?(выход|хватит( болтать| играть)?|выйти|закончить)$', text))


def like_yes(text):
    text = fast_normalize(text)
    return bool(re.match('^(да|ага|окей|ок|конечно|yes|yep|хорошо|ладно)$', text))


def like_no(text):
    text = fast_normalize(text)
    return bool(re.match('^(нет|не|no|nope)$', text))
