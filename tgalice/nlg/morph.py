from tgalice.nlu.basic_nlu import PYMORPHY


def with_number(noun, number):
    text = agree_with_number(noun=noun, number=number)
    return f'{number} {text}'


def agree_with_number(noun, number):
    last = abs(number) % 10
    tens = abs(number) % 100 // 10
    if PYMORPHY:
        parses = PYMORPHY.parse(noun)
        if parses:
            return parses[0].make_agree_with_number(abs(number)).word
    # detect conjugation based on the word ending
    if last == 1:
        return noun
    elif noun.endswith('ка'):
        if last in {2, 3, 4}:
            return noun[:-1] + 'и'
        else:
            return noun[:-1] + 'ек'
    elif noun.endswith('а'):
        if last in {2, 3, 4}:
            return noun[:-1] + 'ы'
        else:
            return noun[:-1]
    else:
        if last in {2, 3, 4}:
            return noun + 'а'
        else:
            return noun + 'ов'


def inflect_case(text, case):
    if PYMORPHY:
        res = []
        for word in text.split():
            parses = PYMORPHY.parse(word)
            word_infl = None
            if parses:
                inflected = parses[0].inflect({case})
                if inflected:
                    word_infl = inflected.word
            res.append(word_infl or word)
        return ' '.join(res)
    return text


def human_duration(hours=0, minutes=0, seconds=0):
    total = hours * 3600 + minutes * 60 + seconds
    s = total % 60
    m = (total // 60) % 60
    h = total // 3600
    parts = []
    if h:
        parts.append(with_number('час', h))
    if m:
        parts.append(with_number('минута', m))
    if s or not h and not m:
        parts.append(with_number('секунда', s))
    return ' '.join(parts)
