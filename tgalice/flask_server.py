from __future__ import print_function

import argparse
import json
import os
import telebot
import warnings

from flask import Flask, request

from .dialog_connector import DialogConnector, SOURCES
from .message_logging import LoggedMessage


class FlaskServer:
    def __init__(
            self,
            connector: DialogConnector,
            telegram_token=None, base_url=None,
            alice_url='alice/', telegram_url='tg/', restart_webhook_url='restart_webhook',
            collection_for_logs=None
    ):
        if telegram_token is None:
            telegram_token = os.environ.get('TOKEN')
        self.telegram_token = telegram_token
        if base_url is None:
            base_url = os.environ.get('BASE_URL')
        self.base_url = base_url
        self.alice_url = alice_url
        self.telegram_url = telegram_url
        self.restart_webhook_url = restart_webhook_url

        self.connector = connector
        self.collection_for_logs = collection_for_logs

        self.app = Flask(__name__)

        self.app.route("/" + self.alice_url, methods=['POST'])(self.alice_response)
        if self.telegram_token is not None:
            self.bot = telebot.TeleBot(telegram_token)
            self.bot.message_handler(func=lambda message: True)(self.tg_response)
            self.app.route('/' + self.telegram_url + self.telegram_token, methods=['POST'])(self.get_tg_message)
            self.app.route("/" + self.restart_webhook_url)(self.telegram_web_hook)
        else:
            self.bot = None

        self._processed_telegram_ids = set()

    def alice_response(self):
        if self.collection_for_logs is not None:
            LoggedMessage.from_alice(request.json).save_to_mongo(self.collection_for_logs)
        response = self.connector.respond(request.json, source=SOURCES.ALICE)
        if self.collection_for_logs is not None:
            LoggedMessage.from_alice(response).save_to_mongo(self.collection_for_logs)
        return json.dumps(response, ensure_ascii=False, indent=2)

    def tg_response(self, message):
        if message.message_id in self._processed_telegram_ids:
            # avoid duplicate response after the bot starts
            # todo: log this event
            return
        self._processed_telegram_ids.add(message.message_id)
        if self.collection_for_logs is not None:
            LoggedMessage.from_telegram(message).save_to_mongo(self.collection_for_logs)
        response = self.connector.respond(message, source=SOURCES.TELEGRAM)
        telegram_response = self.bot.reply_to(message, **response)
        if self.collection_for_logs is not None:
            LoggedMessage.from_telegram(telegram_response).save_to_mongo(self.collection_for_logs)

    def get_tg_message(self):
        self.bot.process_new_updates([telebot.types.Update.de_json(request.stream.read().decode("utf-8"))])
        return "!", 200

    def telegram_web_hook(self):
        self.bot.remove_webhook()
        self.bot.set_webhook(url=self.base_url + self.telegram_url + self.telegram_token)
        return "Weebhook restarted!", 200

    def run_local_telegram(self):
        if self.bot is not None:
            self.bot.polling()
        else:
            raise ValueError('Cannot run Telegram bot, because Telegram token was not found.')

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
