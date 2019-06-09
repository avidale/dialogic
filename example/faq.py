import tgalice


TEXT_HELP = (
    'Привет! Я бот, который умеет работать и в Телеграме и в Алисе.'
    '\nЯ не умею делать примерно ничего, но могу с вами поздороваться.'
    '\nКогда вам надоест со мной говорить, скажите "выход".'
)
TEXT_FAREWELL = 'Всего доброго! Если захотите повторить, скажите "Алиса, включи навык тест tgalice".'


if __name__ == '__main__':
    manager = tgalice.dialog_manager.CascadeDialogManager(
        tgalice.dialog_manager.FAQDialogManager('faq.yaml', matcher='cosine'),
        tgalice.dialog_manager.GreetAndHelpDialogManager(
            greeting_message=TEXT_HELP,
            help_message=TEXT_HELP,
            default_message='Я вас не понимаю.',
            exit_message='Всего доброго! Было приятно с вами пообщаться!'
        )
    )
    connector = tgalice.dialog_connector.DialogConnector(
        dialog_manager=manager,
        storage=tgalice.session_storage.BaseStorage()
    )
    server = tgalice.flask_server.FlaskServer(connector=connector)
    server.parse_args_and_run()
