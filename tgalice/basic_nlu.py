import re


def fast_normalize(text):
    text = re.sub('[^a-zа-я0\-]+', ' ', text.lower())
    text = re.sub('\s+', ' ', text).strip()
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
