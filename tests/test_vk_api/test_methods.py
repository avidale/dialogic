import json
import requests
from unittest.mock import Mock, patch, MagicMock

from tgalice.interfaces.vk import VKBot, VKMessage


@patch('requests.post')
def test_send_message(mock_post: MagicMock):
    mock_post.return_value.status_code = 200
    mock_post.return_value.json = lambda: {}

    bot = VKBot(token='12345', group_id=12345)
    bot.send_message(user_id=666, text='hello', keyboard={'buttons': [[{'action': {'type': 'text', 'label': 'yay'}}]]})
    assert mock_post.called
    args, kwargs = mock_post.call_args
    assert kwargs['url'].endswith('messages.send')
    assert kwargs['data']['user_id'] == 666
    assert kwargs['data']['message'] == 'hello'
    assert kwargs['data']['access_token'] == '12345'
    assert 'group_id' not in kwargs['data']
    assert isinstance(kwargs['data']['keyboard'], str)


def test_apply_handlers():
    bot = VKBot(token='12345', group_id=12345)
    processed1 = []
    processed2 = []
    processed3 = []
    processed4 = []

    @bot.message_handler(regexp='hello')
    def handle1(message: VKMessage):
        processed1.append(message)

    @bot.message_handler(types=['strange_type'])
    def handle2(message: VKMessage):
        processed2.append(message)

    @bot.message_handler(func=lambda x: len(x['object']['message']['text']) == 3)
    def handle3(message: VKMessage):
        processed3.append(message)

    @bot.message_handler()
    def handle4(message: VKMessage):
        processed4.append(message)

    assert len(bot.message_handlers) == 4

    bot.process_new_updates([{'type': 'message_new', 'object': {'message': {'text': 'hello bot'}}}])
    assert len(processed1) == 1
    assert len(processed2) == 0
    assert processed1[0].text == 'hello bot'

    bot.process_new_updates([{'type': 'strange_type', 'object': {'message': {'text': 'hello bot'}}}])
    assert len(processed1) == 1
    assert len(processed2) == 1

    bot.process_new_updates([{'type': 'message_new', 'object': {'message': {'text': 'wow'}}}])
    assert len(processed3) == 1

    bot.process_new_updates([{'type': 'message_new', 'object': {'message': {'text': 'fallback'}}}])
    assert len(processed4) == 1


def test_webhook_processing():
    bot = VKBot(token='12345', group_id=12345)
    bot.webhook_key = 'secret'
    assert bot.process_webhook_data({'type': 'confirmation', 'group_id': 12345}) == ('secret', 200)

    messages = []

    @bot.message_handler()
    def handle(message):
        messages.append(message)

    new_message = {'type': 'message_new', 'object': {'message': {'text': 'hello bot'}}}
    assert bot.process_webhook_data(new_message) == ('ok', 200)
    assert messages[0].text == 'hello bot'


def test_polling():
    bot = VKBot(token='12345', group_id=12345)

    # test setting polling server
    assert bot._polling_server is None
    with patch('requests.get') as mock_get:
        mock_get.return_value.status_code = 200
        mock_get.return_value.json = lambda: {'response': {'server': 'abcd', 'key': 'xyz', 'ts': 23}}
        bot.set_polling_server()
        assert mock_get.called
        assert mock_get.call_args[1]['url'].endswith('groups.getLongPollServer')
        assert bot._polling_server == 'abcd'

    # test actually polling
    with patch('requests.get') as mock_get:
        mock_get.return_value.status_code = 200
        mock_get.return_value.json = lambda: {'updates': ['i am an update'], 'ts': 38}
        assert bot.retrieve_updates() == ['i am an update']
        assert mock_get.called
        assert mock_get.call_args[1]['url'] == 'abcd'
        assert mock_get.call_args[1]['params']['key'] == 'xyz'
        assert mock_get.call_args[1]['params']['ts'] == 23
        assert bot._polling_ts == 38


def test_webhook_remove():
    bot = VKBot(token='12345', group_id=12345)
    with patch('requests.get') as mock_get:
        mock_get.return_value.status_code = 200
        mock_get.return_value.json = lambda: {'response': {'items': [{'id': 17}, {'id': 18}]}}
        bot.remove_webhook()
        assert mock_get.call_count == 3
        assert mock_get.call_args_list[0][1]['url'].endswith('groups.getCallbackServers')
        for call_args, item_id in zip(mock_get.call_args_list[1:], [17, 18]):
            assert call_args[1]['url'].endswith('groups.deleteCallbackServer')
            assert call_args[1]['params']['server_id'] == item_id


def test_webhook_set():
    bot = VKBot(token='12345', group_id=12345)
    assert bot.webhook_key is None
    with patch('requests.get') as mock_get:
        mock_get.return_value.status_code = 200
        mock_get.return_value.json = lambda: {'response': {'code': '777', 'server_id': 13}}
        bot.set_webhook(url='localhost:15777', remove_old=False)
        assert bot.webhook_key == '777'
        assert mock_get.call_count == 3
        assert mock_get.call_args_list[0][1]['url'].endswith('groups.getCallbackConfirmationCode')

        assert mock_get.call_args_list[1][1]['url'].endswith('groups.addCallbackServer')
        assert mock_get.call_args_list[1][1]['params']['secret_key'] == '777'
        assert mock_get.call_args_list[1][1]['params']['url'] == 'localhost:15777'

        assert mock_get.call_args_list[2][1]['url'].endswith('groups.setCallbackSettings')
        assert mock_get.call_args_list[2][1]['params']['server_id'] == 13
