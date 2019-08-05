from __future__ import print_function

import argparse
import json
import logging
import os
import telebot
import warnings

from flask import Flask, request
from pymessenger.bot import Bot as FacebookBot

from .dialog_connector import DialogConnector, SOURCES
from .message_logging import LoggedMessage


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class FlaskServer:
    def __init__(
            self,
            connector: DialogConnector,
            telegram_token=None,
            facebook_access_token=None,
            facebook_verify_token=None,
            base_url=None,
            alice_url='alice/', telegram_url='tg/', facebook_url='fb/',
            restart_webhook_url='restart_webhook',
            collection_for_logs=None, not_log_id=None
    ):
        self.telegram_token = telegram_token or os.environ.get('TOKEN')
        self.facebook_access_token = facebook_access_token or os.environ.get('FACEBOOK_ACCESS_TOKEN')
        self.facebook_verify_token = facebook_verify_token or os.environ.get('FACEBOOK_VERIFY_TOKEN')
        if base_url is None:
            base_url = os.environ.get('BASE_URL')
        self.base_url = base_url
        self.alice_url = alice_url
        self.telegram_url = telegram_url
        self.facebook_url = facebook_url
        self.restart_webhook_url = restart_webhook_url

        self.connector = connector
        self.collection_for_logs = collection_for_logs
        self.not_log_id = not_log_id or set()

        self.app = Flask(__name__)

        logger.info('The Alice webhook is available on "{}"'.format(self.alice_webhook_url))
        self.app.route(self.alice_webhook_url, methods=['POST'])(self.alice_response)

        if self.telegram_token is not None:
            self.bot = telebot.TeleBot(self.telegram_token)
            self.bot.message_handler(func=lambda message: True)(self.tg_response)
            if base_url is not None:
                logger.info('Running Telegram bot with token "{}" on "{}"'.format(
                    self.telegram_token, self.telegram_webhook_url)
                )
                self.app.route(self.telegram_webhook_url, methods=['POST'])(self.get_tg_message)
                self.app.route("/" + self.restart_webhook_url)(self.telegram_web_hook)
            else:
                logger.info(
                    'Running Telegram bot with token "{}", but without BASE_URL it can work only locally'.format(
                        self.telegram_token
                    )
                )
        else:
            logger.info('Running no Telegram bot because TOKEN or BASE_URL was not provided')
            self.bot = None

        if self.facebook_verify_token and self.facebook_access_token:
            logger.info('Running Facebook bot on "{}"'.format(self.facebook_webhook_url))
            self.app.route(self.facebook_webhook_url, methods=['GET'])(self.receive_fb_verification_request)
            self.app.route(self.facebook_webhook_url, methods=['POST'])(self.facebook_response)
            self.facebook_bot = FacebookBot(self.facebook_access_token)
        else:
            logger.info(
                'Running no Facebook bot because FACEBOOK_ACCESS_TOKEN or FACEBOOK_VERIFY_TOKEN was not provided'
            )
            self.facebook_bot = None

        self._processed_telegram_ids = set()

    @property
    def alice_webhook_url(self):
        return "/" + self.alice_url

    @property
    def facebook_webhook_url(self):
        return '/' + self.facebook_url

    @property
    def telegram_webhook_url(self):
        return '/' + self.telegram_url + self.telegram_token

    def log_message(self, data, source, **kwargs):
        # todo: maybe make the logic a part of connector instead of flask server
        if self.collection_for_logs is None:
            return
        if source == SOURCES.ALICE:
            msg = LoggedMessage.from_alice(data, **kwargs)
        elif source == SOURCES.TELEGRAM:
            msg = LoggedMessage.from_telegram(data, **kwargs)
        elif source == SOURCES.FACEBOOK:
            msg = LoggedMessage.from_facebook(data, **kwargs)
        else:
            return
        if self.not_log_id is not None and msg.user_id in self.not_log_id:
            # main reason: don't log pings from Yandex
            return
        msg.save_to_mongo(self.collection_for_logs)

    def alice_response(self):
        self.log_message(request.json, SOURCES.ALICE)
        response = self.connector.respond(request.json, source=SOURCES.ALICE)
        self.log_message(response, SOURCES.ALICE)
        return json.dumps(response, ensure_ascii=False, indent=2)

    def tg_response(self, message):
        if message.message_id in self._processed_telegram_ids:
            # avoid duplicate response after the bot starts
            # todo: log this event
            return
        self._processed_telegram_ids.add(message.message_id)
        self.log_message(message, SOURCES.TELEGRAM)
        response = self.connector.respond(message, source=SOURCES.TELEGRAM)
        multimedia = response.pop('multimedia', [])
        telegram_response = self.bot.reply_to(message, **response)
        response_text = response.pop('text', None)
        # todo: maybe set response['reply_to_message_id'] = message.message_id
        for item in multimedia:
            if item['type'] == 'photo':
                self.bot.send_photo(message.chat.id, photo=item['content'], **response)
            if item['type'] == 'document':
                self.bot.send_document(message.chat.id, data=item['content'], **response)
            elif item['type'] == 'audio':
                self.bot.send_audio(message.chat.id, audio=item['content'], **response)
        self.log_message(telegram_response, SOURCES.TELEGRAM)

    def get_tg_message(self):
        self.bot.process_new_updates([telebot.types.Update.de_json(request.stream.read().decode("utf-8"))])
        return "!", 200

    def telegram_web_hook(self):
        self.bot.remove_webhook()
        self.bot.set_webhook(url=self.base_url + self.telegram_url + self.telegram_token)
        return "Weebhook restarted!", 200

    def run_local_telegram(self):
        if self.bot is not None:
            self.bot.remove_webhook()
            self.bot.polling()
        else:
            raise ValueError('Cannot run Telegram bot, because Telegram token was not found.')

    def receive_fb_verification_request(self):
        """Before allowing people to message your bot, Facebook has implemented a verify token
        that confirms all requests that your bot receives came from Facebook."""
        token_sent = request.args.get("hub.verify_token")
        if token_sent == self.facebook_verify_token:
            return request.args.get("hub.challenge")
        return 'Invalid verification token'

    def facebook_response(self):
        output = request.get_json()
        for event in output['entry']:
            messaging = event['messaging']
            for message in messaging:
                if message.get('message') or message.get('postback'):
                    recipient_id = message['sender']['id']
                    self.log_message(message, SOURCES.FACEBOOK, user_id=recipient_id)
                    if message.get('message', {}).get('text') or message.get('postback'):
                        response = self.connector.respond(message, source=SOURCES.FACEBOOK)
                        self.facebook_bot.send_message(recipient_id, response)
                        self.log_message(response, SOURCES.FACEBOOK, user_id=recipient_id)
                    # if user sends us a GIF, photo,video, or any other non-text item
                    elif message['message'].get('attachments'):
                        pass
                        # todo : do something in case of attachments
        return "Message Processed"

    def run_server(self, host="0.0.0.0", port=None):
        if self.telegram_token is not None:
            self.telegram_web_hook()
        else:
            warnings.warn('Telegram token was not found, running for Alice only.')
        if port is None:
            port = int(os.environ.get('PORT', 5000))
        self.app.run(host=host, port=port)

    def run_command_line(self):
        input_sentence = ''
        while True:
            response, need_to_exit = self.connector.respond(input_sentence, source=SOURCES.TEXT)
            print(response)
            if need_to_exit:
                break
            input_sentence = input('> ')

    def parse_args_and_run(self):
        parser = argparse.ArgumentParser(description='Run the bot')
        parser.add_argument('--cli', action='store_true', help='Run the bot locally in command line mode')
        parser.add_argument('--poll', action='store_true', help='Run the bot locally in polling mode (Telegram only)')
        args = parser.parse_args()
        if args.cli:
            self.run_command_line()
        elif args.poll:
            self.run_local_telegram()
        else:
            self.run_server()
