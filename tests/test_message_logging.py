import pytest
import dialogic
import telebot

from dialogic.storage.database_utils import get_mongo_or_mock


@pytest.fixture
def empty_db():
    database = get_mongo_or_mock()
    database.get_collection('message_logs').drop()
    return database


def test_text_logging_with_connector(empty_db):
    database = empty_db
    input_message = 'hello bot'
    expected_response = 'This is the default message'
    dm = dialogic.dialog_manager.BaseDialogManager(default_message=expected_response)
    connector = dialogic.dialog_connector.DialogConnector(
        dialog_manager=dm,
        log_storage=dialogic.storage.message_logging.MongoMessageLogger(database=database)
    )
    text_response = connector.respond(message=input_message, source=dialogic.SOURCES.TEXT)

    collection = database.get_collection('message_logs')
    logs = list(collection.find())
    assert len(logs) == 2
    first, second = logs

    assert first['text'] == input_message
    assert second['text'] == expected_response

    assert first['source'] == dialogic.SOURCES.TEXT
    assert second['source'] == dialogic.SOURCES.TEXT

    assert first['from_user'] is True
    assert second['from_user'] is False

    assert first['data'] == input_message
    assert second['data'] == text_response


def test_alice_logging_with_connector(empty_db):
    input_message = {
        "meta": {
            "locale": "ru-RU",
            "timezone": "Europe/Moscow",
            "client_id": "ru.yandex.searchplugin/5.80 (Samsung Galaxy; Android 4.4)",
            "interfaces": {
                "screen": {}
            }
        },
        "request": {
            "command": "привет",
            "original_utterance": "привет",
            "type": "SimpleUtterance",
            "markup": {
                "dangerous_context": False
            },
            "payload": {},
            "nlu": {
                "tokens": ["привет"],
                "entities": []
            }
        },
        "session": {
            "new": False,
            "message_id": 4,
            "session_id": "2eac4854-fce721f3-b845abba-20d60",
            "skill_id": "3ad36498-f5rd-4079-a14b-788652932056",
            "user_id": "AC9WC3DF6FCE052E45A4566A48E6B7193774B84814CE49A922E163B8B29881DC"
        },
        "version": "1.0"
    }
    database = empty_db
    expected_response_text = 'This is the default message'
    input_message_text = input_message['request']['command']
    dm = dialogic.dialog_manager.BaseDialogManager(default_message=expected_response_text)
    connector = dialogic.dialog_connector.DialogConnector(
        dialog_manager=dm,
        log_storage=dialogic.storage.message_logging.MongoMessageLogger(database=database)
    )
    alice_response = connector.respond(message=input_message, source=dialogic.SOURCES.ALICE)

    collection = database.get_collection('message_logs')
    logs = list(collection.find())
    assert len(logs) == 2
    first, second = logs

    assert first['text'] == input_message_text
    assert second['text'] == expected_response_text

    assert first['source'] == dialogic.SOURCES.ALICE
    assert second['source'] == dialogic.SOURCES.ALICE

    assert first['from_user'] is True
    assert second['from_user'] is False

    assert first['data'] == input_message
    assert second['data'] == alice_response

    assert first['request_id'] == second['request_id']
    assert first['request_id'] is not None


def test_tg_logging_with_connector(empty_db):
    input_message_text = 'привет'
    input_message = telebot.types.Message(
        message_id=123,
        from_user=telebot.types.User(id=456, first_name='Bob', is_bot=False),
        chat=telebot.types.Chat(username='Bobby', id=123, type='private'),
        date=None, content_type='text', json_string=None,
        options={'text': input_message_text}
    )
    database = empty_db
    expected_response_text = 'This is the default message'
    dm = dialogic.dialog_manager.BaseDialogManager(default_message=expected_response_text)
    connector = dialogic.dialog_connector.DialogConnector(
        dialog_manager=dm,
        log_storage=dialogic.storage.message_logging.MongoMessageLogger(database=database)
    )
    tg_response = connector.respond(message=input_message, source=dialogic.SOURCES.TELEGRAM)

    if 'reply_markup' in tg_response:
        tg_response['reply_markup'] = tg_response['reply_markup'].to_json()

    collection = database.get_collection('message_logs')
    logs = list(collection.find())
    assert len(logs) == 2
    first, second = logs

    assert first['text'] == input_message_text
    assert second['text'] == expected_response_text

    assert first['source'] == dialogic.SOURCES.TELEGRAM
    assert second['source'] == dialogic.SOURCES.TELEGRAM

    assert first['from_user'] is True
    assert second['from_user'] is False

    assert first['data'] == {'message': str(input_message)}
    assert second['data'] == tg_response

    assert first['request_id'] == second['request_id']
    assert first['request_id'] is not None
