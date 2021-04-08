import logging
import os

from flask import Flask, request

from dialogic.interfaces.vk import VKBot, VKMessage

logging.basicConfig(level=logging.INFO)
logging.getLogger('dialogic.interfaces.vk').setLevel(logging.DEBUG)


app = Flask(__name__)


bot = VKBot(
    token=os.environ['VK_TOKEN'],
    group_id=os.environ['VK_GROUP_ID'],
)


@bot.message_handler()
def respond(message: VKMessage):
    bot.send_message(
        peer_id=message.user_id,
        text='Вы написали {}'.format(message.text),
        keyboard={'buttons': [[{'action': {'type': 'text', 'label': 'ок'}}]]},
    )


@app.route('/vk-callback', methods=['POST'])
def respond_to_callback():
    return bot.process_webhook_data(request.json)


if __name__ == '__main__':
    # change this webhook address to the address of your sever
    # if you are running this script locally, you may want to use ngrok to create a tunnel to your local machine
    bot.set_postponed_webhook('https://761c8f3c.eu.ngrok.io/vk-callback', remove_old=True)
    # if debug=True, this code is run twice, which may result in setting two webhooks
    app.run(host='0.0.0.0', port=5000, debug=False)
