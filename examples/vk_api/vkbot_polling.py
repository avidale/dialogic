import logging
import os

from dialogic.interfaces.vk import VKBot, VKMessage

logging.basicConfig(level=logging.DEBUG)

bot = VKBot(
    token=os.environ['VK_TOKEN'],
    group_id=os.environ['VK_GROUP_ID'],
    polling_wait=3,  # normally, timeout is about 20 seconds, but we make it shorter for quicker feedback
)


@bot.message_handler()
def respond(message: VKMessage):
    bot.send_message(
        peer_id=message.user_id,
        text='Вы написали {}'.format(message.text),
        keyboard={
            'one_time': True,
            'buttons': [[{
                'action': {'type': 'text', 'label': 'окей'},
                'color': 'secondary',
            }]]
        },
    )


if __name__ == '__main__':
    bot.polling()
