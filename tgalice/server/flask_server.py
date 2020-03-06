from __future__ import print_function

import argparse
import json
import logging
import os
import telebot
import warnings

from flask import Flask, request
from pymessenger.bot import Bot as FacebookBot

from tgalice.dialog_connector import DialogConnector, SOURCES


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
            app=None,
    ):
        self.telegram_token = telegram_token or os.environ.get('TOKEN') or os.environ.get('TELEGRAM_TOKEN')
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

        self.app = app or Flask(__name__)

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

    def alice_response(self):
        logger.info('Got message from Alice: {}'.format(request.json))
        response = self.connector.respond(request.json, source=SOURCES.ALICE)
        logger.info('Sending message to Alice: {}'.format(response))
        return json.dumps(response, ensure_ascii=False, indent=2)

    def tg_response(self, message):
        logger.info('Got message from Telegram: {}'.format(message))
        if message.message_id in self._processed_telegram_ids:
            # avoid duplicate response after the bot starts
            logger.info('Telegram message id {} is duplicate, skipping it'.format(message.message_id))
            return
        self._processed_telegram_ids.add(message.message_id)
        # todo: cleanup old ids from _processed_telegram_ids
        response = self.connector.respond(message, source=SOURCES.TELEGRAM)
        telegram_response = self.bot.reply_to(message, **response)
        multimedia = response.pop('multimedia', [])
        for item in multimedia:
            if item['type'] == 'photo':
                self.bot.send_photo(message.chat.id, photo=item['content'], **response)
            if item['type'] == 'document':
                self.bot.send_document(message.chat.id, data=item['content'], **response)
            elif item['type'] == 'audio':
                self.bot.send_audio(message.chat.id, audio=item['content'], **response)
        logger.info('Sent a response to Telegram: {}'.format(message))

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
        logger.info('Got messages from Facebook: {}'.format(output))
        for event in output['entry']:
            messaging = event['messaging']
            for message in messaging:
                if message.get('message') or message.get('postback'):
                    recipient_id = message['sender']['id']
                    response = self.connector.respond(message, source=SOURCES.FACEBOOK)
                    logger.info('Sending message to Facebook: {}'.format(response))
                    self.facebook_bot.send_message(recipient_id, response)
        return "Message Processed"

    def run_server(self, host="0.0.0.0", port=None, use_ngrok=False):
        if use_ngrok:
            from tgalice.server.flask_ngrok import run_with_ngrok
            run_with_ngrok(self.app)
        if self.telegram_token is not None and self.base_url is not None:
            self.telegram_web_hook()
        else:
            warnings.warn('Either telegram token or base_url was not found; cannot run Telegram bot.')
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
        parser.add_argument('--ngrok', action='store_true',
                            help='Run the bot locally with ngrok tunnel into the Internet')
        args = parser.parse_args()
        if args.cli:
            self.run_command_line()
        elif args.poll:
            self.run_local_telegram()
        else:
            self.run_server(use_ngrok=args.ngrok)
