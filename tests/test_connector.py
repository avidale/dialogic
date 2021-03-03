import pytest

from dialogic import COMMANDS
from dialogic.adapters import SalutAdapter
from dialogic.dialog_connector import DialogConnector, SOURCES
from dialogic.dialog_manager import BaseDialogManager, Response


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
    alice_message['session']['user'] = {'user_id': '123'}
    uo = {'count': 1, 'name': 'Alex'}
    response = Response(text='привет', user_object=uo)
    output = connector.standardize_output(source=SOURCES.ALICE, original_message=alice_message, response=response)
    assert output['user_state_update'] == {'count': 1, 'name': 'Alex'}
    assert output.get('application_state') is None


def test_save_user_object_by_yandex_to_user_unauthorized(alice_message):
    connector = DialogConnector(Repeater(), alice_native_state='user')
    uo = {'count': 1, 'name': 'Alex'}
    response = Response(text='привет', user_object=uo)
    output = connector.standardize_output(source=SOURCES.ALICE, original_message=alice_message, response=response)
    assert output['user_state_update'] == {'count': 1, 'name': 'Alex'}
    assert output['application_state'] == {'count': 1, 'name': 'Alex'}


@pytest.mark.parametrize('ans,uo,auth', [
    (True, {
        'session': {'value': 10},
        'user': {'value': 42},
        'application': {'value': 50}
    }, True),
    ('session', {'value': 10}, True),
    ('user', {'value': 42}, True),
    ('user', {'value': 50}, False),
    (False, {}, True),
])
def test_load_user_object_by_yandex(ans, uo, auth, alice_message):
    connector = DialogConnector(Repeater(), alice_native_state=ans)
    if auth:
        alice_message['session']['user'] = {'user_id': '123'}
    alice_message['state'] = {
        'session': {
            'value': 10
        },
        'user': {
            'value': 42,
        },
        'application': {
            'value': 50,
        }
    }
    ctx = connector.make_context(message=alice_message, source=SOURCES.ALICE)
    assert ctx.user_object == uo


@pytest.fixture
def salut_req():
    result = {
        'messageId': 1614362356647,
        'sessionId': 'a298a38a-faa8-442f-97fd-1a53555c6d26',
        'messageName': 'MESSAGE_TO_SKILL',
        'payload': {
            'applicationId': '975dd918-8833-42ff-8c4f-d97dadb3368f',
            'appversionId': 'afda44e3-72dd-4d63-9cf6-3e6371e0d775',
            'projectName': 'b64d2304-20ea-4bc5-8e82-0b194bf79be8',
            'intent': 'run_app',
            'original_intent': 'axon',
            'intent_meta': {},
            'message': {
                'original_text': 'настоящий',
                'normalized_text': 'настоящий .',
                'tokenized_elements_list': [
                    {
                        'text': 'настоящий',
                        'raw_text': 'настоящий',
                        'grammem_info': {
                            'case': 'nom',
                            'degree': 'pos',
                            'gender': 'masc',
                            'number': 'sing',
                            'raw_gram_info': 'case=nom|degree=pos|gender=masc|number=sing',
                            'part_of_speech': 'ADJ'
                        },
                        'lemma': 'настоящий',
                        'is_stop_word': False,
                        'list_of_dependents': [],
                        'dependency_type': 'root',
                        'head': 0
                    },
                    {
                        'raw_text': '.',
                        'text': '.',
                        'lemma': '.',
                        'token_type': 'SENTENCE_ENDPOINT_TOKEN',
                        'token_value': {'value': '.'},
                        'list_of_token_types_data': [
                            {
                                'token_type': 'SENTENCE_ENDPOINT_TOKEN',
                                'token_value': {
                                    'value': '.'}}]
                    }],
                'entities': {},
                'original_message_name': 'MESSAGE_FROM_USER',
                'human_normalized_text': 'настоящий',
                'asr_normalized_message': None,
                'human_normalized_text_with_anaphora': 'настоящий'},
            'device': {'platformType': 'web', 'platformVersion': '1',
                       'surface': 'SBERBOX', 'surfaceVersion': '1',
                       'deviceId': '', 'deviceManufacturer': '',
                       'deviceModel': ''},
            'app_info': {
                'projectId': 'e4f4a982-f80d-47cc-89d2-3321fe2b11fd',
                'applicationId': '975dd918-8833-42ff-8c4f-d97dadb3368f',
                'appversionId': 'afda44e3-72dd-4d63-9cf6-3e6371e0d775',
                'systemName': None,
                'frontendEndpoint': None,
                'frontendType': 'DIALOG'
            }, 'annotations': {
                'censor_data': {'classes': ['politicians', 'obscene', 'model_response'],
                                'probas': [0, 0, 0.006988049950450659]},
                'text_sentiment': {'classes': ['negative', 'positive', 'neutral'],
                                   'probas': [0.000301319727441296, 0.06846659630537033, 0.9312320351600647]},
                'asr_sentiment': {'classes': [], 'probas': []}
            },
            'selected_item': {},
            'new_session': False,
            'strategies': {'last_call': None},
            'character': {'id': 'sber', 'name': 'Сбер', 'gender': 'male', 'appeal': 'official'},
            'meta': {'current_app': {}, 'time': {}},
            'asr': {}
        },
        'uuid': {
            'userId': '803de100-edd6-41d8-6d77',
            'sub': 'wXjow3XPPKlnD6lq4EnEIIimjqieg4hilLy8PZvF++',
            'userChannel': 'B2C'
        }
    }
    return result


def test_salut_request(salut_req):
    adapter = SalutAdapter()
    ctx = adapter.make_context(salut_req)
    assert ctx.message_text == 'настоящий'


def test_salut_response(salut_req):
    adapter = SalutAdapter()
    response = Response(
        text='kek',
        voice='brekekek',
        suggests=['yes', 'no'],
        commands=[COMMANDS.EXIT],
        links=[{'title': 'click me', 'url': 'www.com'}]
    )
    result = adapter.make_response(response=response, original_message=salut_req)
    assert len(result['uuid']) == 3
    assert result['payload']['pronounceText'] == 'brekekek'
    assert result['payload']['items'] == [{'bubble': {'text': 'kek'}}]
    assert len(result['payload']['suggestions']['buttons']) == 3
    assert 'device' in result['payload']
    assert result['payload']['finished'] is True
