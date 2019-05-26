import argparse
import tgalice as ta


TEXT_HELP = (
    'Привет! Я бот, который умеет работать и в Телеграме и в Алисе.'
    '\nПоскольку это пример, я просто повторяю ваши слова и считаю ваши сообщения.'
    '\nКогда вам надоест, скажите "довольно" или "Алиса, хватит".'
)
TEXT_FAREWELL = 'Всего доброго! Если захотите повторить, скажите "Алиса, включи навык тест tgalice".'


class ExampleDialogManager(ta.dialog_manager.BaseDialogManager):
    def respond(self, user_object, message_text, metadata):
        suggests = ['довольно']
        count = user_object.get('count', 0) + 1
        commands = []
        text = ta.basic_nlu.fast_normalize(message_text)

        if not text or ta.basic_nlu.like_help(text) or not user_object or text == '/start':
            response = TEXT_HELP
        elif text == 'довольно' or ta.basic_nlu.like_exit(text):
            response = TEXT_FAREWELL
            commands.append(ta.dialog_manager.COMMANDS.EXIT)
        else:
            response = 'Вы только что сказали "{}". Всего вы сказали {}.'.format(message_text, self._count(count))

        user_object['count'] = count
        return user_object, response, suggests, commands

    @staticmethod
    def _count(count):
        ones = count % 10
        tens = (count // 10) % 10
        if ones == 1 and tens != 1:
            return '{} команду'.format(count)
        elif ones in {2, 3, 4} and tens != 1:
            return '{} команды'.format(count)
        else:
            return '{} команд'.format(count)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Run the bot')
    parser.add_argument('--poll', action='store_true', help='Run the bot locally in polling mode (Telegram only)')
    args = parser.parse_args()
    connector = ta.dialog_connector.DialogConnector(
        dialog_manager=ExampleDialogManager(),
        storage=ta.session_storage.BaseStorage()
    )
    server = ta.flask_server.FlaskServer(connector=connector)
    if args.poll:
        server.run_local_telegram()
    else:
        server.run_server()
