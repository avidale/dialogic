import copy

from tgalice import basic_nlu
from tgalice.dialog_manager import BaseDialogManager, COMMANDS


TEXT_HELP = (
    'Привет! Я бот, который умеет работать и в Телеграме и в Алисе.'
    '\nПоскольку это пример, я просто повторяю ваши слова'
    '\nКогда вам надоест, скажите "довольно" или "Алиса, хватит".'
)
TEXT_FAREWELL = 'Всего доброго! Если захотите повторить, скажите "Алиса, включи навык тест tgalice".'

COMMAND_EXIT = 'exit'


class ExampleDialogManager(BaseDialogManager):
    def respond(self, user_object, message_text, metadata):
        suggests = ['довольно']
        updated_user_object = copy.deepcopy(user_object)
        commands = []
        text = basic_nlu.fast_normalize(message_text)
        if not text or basic_nlu.like_help(text) or not updated_user_object or text == '/start':
            response = TEXT_HELP
        elif text == 'довольно' or basic_nlu.like_exit(text):
            response = TEXT_FAREWELL
            commands.append(COMMAND_EXIT)
        else:
            response = 'Вы только что сказали "{}"'.format(message_text)
        updated_user_object['last_dialog'] = [text, response]
        return updated_user_object, response, suggests, commands
