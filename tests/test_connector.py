import pytest

from tgalice.dialog_connector import DialogConnector, SOURCES
from tgalice.dialog_manager import BaseDialogManager, Response


class Repeater(BaseDialogManager):
    def respond(self, ctx):
        return Response(text=ctx.message_text)


@pytest.fixture
def alice_message():
    return {
        'meta': {
            'client_id': 'ru.yandex.searchplugin/7.16 (none none; android 4.4.2)',
            'interfaces': {
                'account_linking': {},
                'payments': {},
                'screen': {}
            },
            'locale': 'ru-RU',
            'timezone': 'UTC'
        },
        'request': {
            'command': 'привет',
            'nlu': {
                'entities': [],
                'tokens': ['привет']
            },
            'original_utterance': 'передай тестовому навыку привет',
            'type': 'SimpleUtterance'
        },
        'session': {
            'message_id': 0,
            'new': True,
            'session_id': 'session-1',
            'skill_id': 'skill-1',
            'user_id': 'user-id-1'
        },
        'version': '1.0'
    }


def test_alice_input(alice_message):
    connector = DialogConnector(Repeater())
    ctx = connector.make_context(message=alice_message, source=SOURCES.ALICE)
    assert ctx.user_id == 'alice__user-id-1'
    assert ctx.message_text == 'привет'
    assert ctx.metadata['new_session']


def test_alice_response(alice_message):
    connector = DialogConnector(Repeater())
    response = Response(text='привет', suggests=['тебе тоже'])
    output = connector.standardize_output(source=SOURCES.ALICE, original_message=alice_message, response=response)
    assert not output['response'].get('end_session')
    assert output['response']['text'] == 'привет'
    assert 'voice' not in output['response'] or output['response']['voice'] == 'привет'
    assert output['response']['buttons'] == [{'title': 'тебе тоже', 'hide': True}]


def test_user_objects():
    connector = DialogConnector(Repeater())
    assert connector.get_user_object('user_1') == {}
    connector.set_user_object('user_1', {'name': 'alex'})
    assert connector.get_user_object('user_2') == {}
    assert connector.get_user_object('user_1') == {'name': 'alex'}


def test_save_user_object_by_yandex(alice_message):
    connector = DialogConnector(Repeater(), alice_native_state=True)
    uo = {
        'session': {'count': 1},
        'user': {'name': 'Alex'}
    }
    response = Response(text='привет', user_object=uo)
    output = connector.standardize_output(source=SOURCES.ALICE, original_message=alice_message, response=response)
    assert output['session_state'] == {'count': 1}
    assert output['user_state_update'] == {'name': 'Alex'}


def test_save_user_object_by_yandex_to_session(alice_message):
    connector = DialogConnector(Repeater(), alice_native_state='session')
    uo = {'count': 1, 'name': 'Alex'}
    response = Response(text='привет', user_object=uo)
    output = connector.standardize_output(source=SOURCES.ALICE, original_message=alice_message, response=response)
    assert output['session_state'] == {'count': 1, 'name': 'Alex'}


def test_save_user_object_by_yandex_to_user(alice_message):
    connector = DialogConnector(Repeater(), alice_native_state='user')
    uo = {'count': 1, 'name': 'Alex'}
    response = Response(text='привет', user_object=uo)
    output = connector.standardize_output(source=SOURCES.ALICE, original_message=alice_message, response=response)
    assert output['user_state_update'] == {'count': 1, 'name': 'Alex'}


@pytest.mark.parametrize('ans,uo', [
    (True, {
        'session': {'value': 10},
        'user': {'value': 42}
    }),
    ('session', {'value': 10}),
    ('user', {'value': 42}),
    (False, {}),
])
def test_load_user_object_by_yandex(ans, uo, alice_message):
    connector = DialogConnector(Repeater(), alice_native_state=ans)
    alice_message['state'] = {
        'session': {
            'value': 10
        },
        'user': {
            'value': 42,
        }
    }
    ctx = connector.make_context(message=alice_message, source=SOURCES.ALICE)
    assert ctx.user_object == uo
