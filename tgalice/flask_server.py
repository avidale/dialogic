import json
import os
import telebot

from flask import Flask, request
from tgalice.dialog_connector import DialogConnector


class FlaskServer:
    def __init__(
            self,
            connector: DialogConnector,
            telegram_token=None, base_url=None,
            alice_url='alice/', telegram_url='tg/', restart_webhook_url='restart_webhook'
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

        self.bot = telebot.TeleBot(telegram_token)
        self.connector = connector
        self.app = Flask(__name__)

        self.bot.message_handler(func=lambda message: True)(self.tg_response)
        self.app.route("/" + self.alice_url, methods=['POST'])(self.alice_response)
        self.app.route('/' + self.telegram_url + self.telegram_token, methods=['POST'])(self.get_tg_message)
        self.app.route("/" + self.restart_webhook_url)(self.telegram_web_hook)

    def alice_response(self):
        response = self.connector.respond(request.json, source='alice')
        return json.dumps(response, ensure_ascii=False, indent=2)

    def tg_response(self, message):
        response = self.connector.respond(message, source='telegram')
        self.bot.reply_to(message, **response)

    def get_tg_message(self):
        self.bot.process_new_updates([telebot.types.Update.de_json(request.stream.read().decode("utf-8"))])
        return "!", 200

    def telegram_web_hook(self):
        self.bot.remove_webhook()
        self.bot.set_webhook(url=self.base_url + self.telegram_url + self.telegram_token)
        return "Weebhook restarted!", 200

    def run_local_telegram(self):
        self.bot.polling()

    def run_server(self, host="0.0.0.0", port=None):
        self.telegram_web_hook()
        if port is None:
            port = int(os.environ.get('PORT', 5000))
        self.app.run(host=host, port=port)
