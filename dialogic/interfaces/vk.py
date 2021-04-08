import json
import logging
import random
import re
import requests
import threading
import time


logger = logging.getLogger(__name__)

VK_API_URL = 'https://api.vk.com/method/'


class VKBot:
    def __init__(
            self, token, group_id, api_version='5.103', polling_freq=5, polling_wait=25, webhook_key=None,
            dont_parse_links=True,
    ):
        self.token = token
        self.group_id = group_id
        self.api_version = api_version
        self.message_handlers = []
        self._polling_key = None
        self._polling_server = None
        self._polling_ts = None
        self.polling_freq = polling_freq
        self.polling_wait = polling_wait
        self.webhook_key = webhook_key
        self.dont_parse_links = dont_parse_links

    def polling(self):
        """ Start long polling with wait timeout self.polling_wait and interval self.polling_freq """
        self.set_polling_server()
        while True:
            updates = self.retrieve_updates()
            logging.debug('got {} new updates from polling'.format(len(updates)))
            self.process_new_updates(updates=updates)
            time.sleep(self.polling_freq)

    def set_polling_server(self):
        """ Prepare the requisites for long polling """
        j = self._request_api('groups.getLongPollServer')['response']
        self._polling_server = j['server']
        self._polling_key = j['key']
        self._polling_ts = j['ts']

    def retrieve_updates(self):
        """ Do one iteration of long polling and return a list of fresh updates """
        assert self._polling_server is not None
        logger.info('Start retrieving polling updates...')
        result = requests.get(
            url=self._polling_server,
            params={
                'act': 'a_check',
                'key': self._polling_key,
                'ts': self._polling_ts,
                'wait': self.polling_wait,
                'v': self.api_version,  # it's undocumented, so I'm not sure it always works as expected
            },
        )
        self._fail_on_bad_response('retrieve long poll', result)
        j = result.json()
        self._polling_ts = j['ts']
        updates = j['updates']  # each update looks like {'type': update_type, 'object': the message}
        return updates

    def process_new_updates(self, updates):
        """ Take a list of raw updates, and apply the first relevant handler to each one """
        for update in updates:
            logger.debug('processing an update: {}'.format(update))
            for handler in self.message_handlers:
                if self._apply_filters(filters=handler['filters'], update=update):
                    handler['function'](update)
                    break  # only one handler is supposed to be triggered

    @staticmethod
    def _apply_filters(filters, update):
        for filter_type, filter_value in filters.items():
            if filter_value is None:
                continue
            if filter_type == 'types':
                if update.get('type') not in filter_value:
                    return False
            elif filter_type == 'regexp':
                if not re.search(filter_value, extract_message_text(update), re.IGNORECASE):
                    return False
            elif filter_type == 'func':
                if not filter_value(update):
                    return False
            else:
                raise ValueError('Filter type {} is invalid'.format(filter_type))
        return True

    def remove_webhook(self, webhook_id=None):
        """ Remove all callback webhooks from the group (default), or one or several specific webhooks """
        if webhook_id is None:
            result = self._request_api('groups.getCallbackServers')
            if 'response' in result:
                webhook_ids = [server['id'] for server in result['response']['items']]
            else:
                logger.debug(f'vk callback servers response is {result}')
                webhook_ids = []
        elif isinstance(webhook_id, int):
            webhook_ids = [webhook_id]
        else:
            # assume it's a list of ids
            webhook_ids = webhook_id

        for server_id in webhook_ids:
            logger.debug('removing server {}'.format(server_id))
            self._request_api('groups.deleteCallbackServer', server_id=server_id)

    def _get_webhook_secret_code(self):
        logger.info('looking for webhook secret code...')
        j = self._request_api('groups.getCallbackConfirmationCode')
        if 'response' in j:
            return j['response']['code']
        else:
            logger.debug(f'vk webhook secret code response is {j}')
            return

    def set_webhook(self, url, secret_key=None, title='default hook', remove_old=True, events=None):
        """ Create a webhook to the specified URL.
        By default, it is triggered by new messages, but a map of triggers may be set in `events`.
        By default, all the existing webhooks are removed, but it can be turned off by setting `remove_old=False`.
        The list of triggers is given at https://vk.com/dev/groups.setCallbackSettings
        """
        if remove_old:
            # todo: deal with concurrency (e.g. werkzeug restarts)
            self.remove_webhook()
        if secret_key is None:
            secret_key = self.webhook_key
        if secret_key is None:
            secret_key = self._get_webhook_secret_code()
            self.webhook_key = secret_key
        if events is None:
            events = {'message_new': 1}

        logger.info('setting webhook...')
        assert len(title) < 14
        j = self._request_api('groups.addCallbackServer', url=url, title=title, secret_key=secret_key)
        logger.info('webhook creation data: {}'.format(j))
        server_id = j['response']['server_id']

        logger.info('attaching incoming messages to webhook...')
        return self._request_api(
            'groups.setCallbackSettings',
            server_id=server_id,
            api_version=self.api_version,  # version of the proposed callback api
            secret_key=secret_key,
            **events
        )

    def set_postponed_webhook(self, url, secret_key=None, interval=1, remove_old=True):
        """ Run `set_webhook`, as soon as the webhook url starts responding """
        def runner():
            while True:
                logger.info('checking webhook availability...')
                result = requests.post(url, json={'type': 'confirmation', 'group_id': self.group_id, 'fake': True})
                if result.status_code == 200:
                    break
                time.sleep(interval)
            self.set_webhook(url=url, secret_key=secret_key, remove_old=remove_old)
        thread = threading.Thread(target=runner, daemon=True)
        thread.start()

    def message_handler(self, types=None, regexp=None, func=None):
        """ This decorator registers the function as a handler for certain type of messages """
        if types is None:
            types = ['message_new']

        def decorator(handler):
            def new_handler(raw_message):
                if isinstance(raw_message, VKMessage):
                    new_message = raw_message
                else:
                    new_message = VKMessage.from_json(raw_message)
                return handler(new_message)

            self.message_handlers.append({
                'function': new_handler,
                'filters': {'types': types, 'regexp': regexp, 'func': func}
            })
            return new_handler
        return decorator

    def send_message(self, peer_id=None, user_id=None, text='-', keyboard=None, reply_to=None):
        """ Send the message with the specified text to the specified user. """
        if peer_id is None:
            peer_id = user_id
        extras = {}
        if keyboard is not None:
            if not isinstance(keyboard, str):
                keyboard = json.dumps(keyboard)
            extras['keyboard'] = keyboard
        if reply_to is not None:
            extras['reply_to'] = reply_to
        if self.dont_parse_links is not None:
            extras['dont_parse_links'] = int(self.dont_parse_links)
        result = self._request_api(
            'messages.send',
            request_method='POST',
            user_id=peer_id,
            message=text,
            random_id=random.randint(0, 1_000_000_000_000_000_000),
            group_id=None,  # pass it explicitly, to avoid confusion with user_id
            **extras,
        )
        logger.debug('message sending result: {}'.format(result))
        return result

    def _request_api(self, method, request_method='GET', **params):
        special_params = {
            'access_token': self.token,
            'v': self.api_version,
            'group_id': self.group_id,
        }
        for k, v in special_params.items():
            if k not in params:
                params[k] = v
        payload = {k: v for k, v in params.items() if v is not None}
        url = VK_API_URL + method
        if request_method == 'GET':
            result = requests.get(url=url, params=payload)
        else:  # assume it is 'POST'
            result = requests.post(url=url, data=payload)
        self._fail_on_bad_response(method, result)
        return result.json()

    @staticmethod
    def _fail_on_bad_response(request_goal, response):
        if response.status_code != 200:
            raise ValueError('Request to {} returned error code {}, with contents "{}".'.format(
                request_goal, response.status_code, response.text
            ))

    def process_webhook_data(self, data):
        """ Take the object passed into webhook, process updates, and return the appropriate answer and code
        The webhook answer serves two roles:
            1. When `type=confirmation`, it confirms its validity to the VK backend when registering webhook
            2. Otherwise, it pushes new updates into the message handlers (or elsewhere)
        """
        logger.debug('Got callback data: {}'.format(data))
        if data.get('type') == 'confirmation' and str(data.get('group_id')) == str(self.group_id):
            logger.debug('Telling the callback secret to VK!')
            return self.webhook_key or '', 200
        self.process_new_updates([data])
        return 'ok', 200  # todo: async?

    def register_flask_webhook(self, app, endpoint):
        """ Attach its own webhook to the given endpoint of the given flask app """
        from flask import request
        app.route(endpoint, methods=['POST'])(lambda: self.process_webhook_data(request.json))


def extract_message_text(update):
    # todo: extract message text in a consistent way
    message = update['object']
    if 'message' in message:
        message = message['message']
    return message.get('body') or message.get('text') or ''


class VKMessage:
    """
    Source: personal messages, like https://vk.com/dev/objects/message -
    When it comes from webhook, it looks like
        {"type": "message_new", "object": object, "group_id": 12345}
    where object is
        {"message": personal_message, "client_info": client_info}
    when it comes from long poll, it looks like the old version of API, so the format is different
    # todo: add message_id, attachments, date, etc.
    """
    def __init__(self, user_id, text, peer_id, action=None, data=None):
        self.user_id = user_id
        self.peer_id = peer_id
        self.text = text
        self.action = action
        self.data = data

    @classmethod
    def from_json(cls, data):
        message = data['object']

        if 'message' in message:
            message = message['message']

        text = message.get('body') or message.get('text') or ''
        user_id = message.get('user_id') or message.get('from_id')
        peer_id = message.get('peer_id') or user_id
        action = message.get('action')
        return cls(user_id=user_id, text=text, peer_id=peer_id, action=action, data=message)

    def to_json(self):
        return {'text': self.text, 'user_id': self.user_id}
