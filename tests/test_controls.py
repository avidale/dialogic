import tgalice.nlg.controls as ctrl


def test_simple_button():
    data = {
        "title": 'button title'
    }
    button = ctrl.Button(**data)
    data['hide'] = True
    assert button.to_dict() == data


def test_fixed_button_with_url():
    data = {
        'title': 'button title',
        'url': 'https://example.com/',
        'hide': False
    }
    button = ctrl.Button(**data)
    assert button.to_dict() == data
