import tgalice


TEXT_HELP = (
    'Привет! Я бот, который умеет работать и в Телеграме и в Алисе.'
    '\nПоскольку это пример, я просто повторяю ваши слова и считаю ваши сообщения.'
    '\nКогда вам надоест, скажите "довольно" или "Алиса, хватит".'
)
TEXT_FAREWELL = 'Всего доброго! Если захотите повторить, скажите "Алиса, включи навык тест tgalice".'


class ExampleDialogManager(tgalice.dialog_manager.BaseDialogManager):
    def respond(self, user_object, message_text, metadata):
        suggests = ['довольно']
        count = user_object.get('count', -1) + 1
        commands = []
        text = tgalice.nlu.basic_nlu.fast_normalize(message_text)

        if not text or tgalice.nlu.basic_nlu.like_help(text) or not user_object or text == '/start':
            response = TEXT_HELP
        elif text == 'довольно' or tgalice.nlu.basic_nlu.like_exit(text):
            response = TEXT_FAREWELL
            commands.append(tgalice.dialog_manager.COMMANDS.EXIT)
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
    connector = tgalice.dialog_connector.DialogConnector(
        dialog_manager=ExampleDialogManager(),
        storage=tgalice.session_storage.BaseStorage()
    )
    server = tgalice.flask_server.FlaskServer(connector=connector)
    server.parse_args_and_run()
