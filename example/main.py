import argparse
import json
import logging
import os
import telebot

from flask import Flask, request
from tgalice.dialog_connector import DialogConnector
from tgalice.session_storage import BaseStorage

from .logic import ExampleDialogManager

logging.basicConfig(level=logging.DEBUG)

TOKEN = os.environ.get('TOKEN')
TELEBOT_URL = 'telebot_webhook/'
ALICE_URL = 'alice/'
BASE_URL = os.environ.get('BASE_URL')


bot = telebot.TeleBot(TOKEN)
connector = DialogConnector(dialog_manager=ExampleDialogManager(), storage=BaseStorage())
app = Flask(__name__)


@app.route("/" + ALICE_URL, methods=['POST'])
def alice_response():
    logging.info('Alice request: %r', request.json)
    response = connector.respond(request.json, source='alice')
    logging.info('Alice response: %r', response)
    return json.dumps(
        response,
        ensure_ascii=False,
        indent=2
    )


@bot.message_handler(func=lambda message: True)
def echo_all(message):
    response = connector.respond(message, source='telegram')
    # log_message(message, response)
    print('message was "{}"'.format(message.text))
    bot.reply_to(message, **response)


@app.route('/' + TELEBOT_URL + TOKEN, methods=['POST'])
def get_message():
    bot.process_new_updates([telebot.types.Update.de_json(request.stream.read().decode("utf-8"))])
    return "!", 200


@app.route("/restart_webhook")
def telegram_web_hook():
    bot.remove_webhook()
    bot.set_webhook(url=BASE_URL + TELEBOT_URL + TOKEN)
    return "Weebhook restarted!", 200


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Run the bot')
    parser.add_argument('--poll', action='store_true', help="Run the bot locally in polling mode (Telegram only)")
    args = parser.parse_args()
    if args.poll:
        bot.polling()
    else:
        telegram_web_hook()
        app.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5000)))
