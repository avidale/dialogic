from dialogic.nlg.reply_markup import TTSParser
from dialogic.dialog_manager.base import Response

PARSED_RESPONSE = dict(
    markup='This markup be used in <text>Yandex.Dialogs</text><voice>Yandex Dialogs</voice> and other platforms.'
           '<a href="https://dialogs.yandex.ru/">Yandex.Dialogs site</a>',
    expected_text='This markup be used in Yandex.Dialogs and other platforms.',
    expected_voice='This markup be used in Yandex Dialogs and other platforms.',
    expected_links=[{'title': 'Yandex.Dialogs site', 'url': 'https://dialogs.yandex.ru/'}],
)


def test_tts_parser():
    parser = TTSParser()
    parser.feed(PARSED_RESPONSE['markup'])
    assert parser.get_text() == PARSED_RESPONSE['expected_text']
    assert parser.get_voice() == PARSED_RESPONSE['expected_voice']
    assert parser.get_links() == PARSED_RESPONSE['expected_links']


def test_response_set_text():
    resp = Response(text=None).set_text(PARSED_RESPONSE['markup'])
    assert resp.text == PARSED_RESPONSE['expected_text']
    assert resp.voice == PARSED_RESPONSE['expected_voice']
    assert resp.links == PARSED_RESPONSE['expected_links']
