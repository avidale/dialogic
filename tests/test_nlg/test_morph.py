from dialogic.nlg.morph import inflect_case, with_number, human_duration


def test_inflect_case():
    assert inflect_case('жук', 'datv') == 'жуку'


def test_with_number():
    assert with_number('слон', 0) == '0 слонов'
    assert with_number('слон', 1) == '1 слон'
    assert with_number('слон', 2) == '2 слона'
    assert with_number('слон', 5) == '5 слонов'


def test_duration():
    assert human_duration(hours=1, minutes=2, seconds=5) == '1 час 2 минуты 5 секунд'
    assert human_duration() == '0 секунд'
    assert human_duration(minutes=22) == '22 минуты'
