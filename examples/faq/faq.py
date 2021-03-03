import dialogic
import logging

logging.basicConfig(level=logging.DEBUG)


TEXT_HELP = (
    'Привет! Я бот, который умеет работать и в Телеграме и в Алисе.'
    '\nЯ не умею делать примерно ничего, но могу с вами поздороваться.'
    '\nКогда вам надоест со мной говорить, скажите "выход".'
)
TEXT_FAREWELL = 'Всего доброго! Если захотите повторить, скажите "Алиса, включи навык тест dialogic".'


if __name__ == '__main__':
    manager = dialogic.dialog_manager.CascadeDialogManager(
        dialogic.dialog_manager.FAQDialogManager('faq.yaml', matcher='cosine'),
        dialogic.dialog_manager.GreetAndHelpDialogManager(
            greeting_message=TEXT_HELP,
            help_message=TEXT_HELP,
            default_message='Я вас не понимаю.',
            exit_message='Всего доброго! Было приятно с вами пообщаться!'
        )
    )
    connector = dialogic.dialog_connector.DialogConnector(
        dialog_manager=manager,
        storage=dialogic.storage.session_storage.BaseStorage()
    )
    server = dialogic.server.flask_server.FlaskServer(connector=connector)
    server.parse_args_and_run()
