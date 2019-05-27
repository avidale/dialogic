import argparse
import tgalice as ta


TEXT_HELP = (
    'Привет! Я бот, который умеет работать и в Телеграме и в Алисе.'
    '\nПоскольку это пример, я просто повторяю ваши слова и считаю ваши сообщения.'
    '\nКогда вам надоест, скажите "довольно" или "Алиса, хватит".'
)
TEXT_FAREWELL = 'Всего доброго! Если захотите повторить, скажите "Алиса, включи навык тест tgalice".'


parser = argparse.ArgumentParser(description='Run the bot')
parser.add_argument('--poll', action='store_true', help='Run the bot locally in polling mode (Telegram only)')
args = parser.parse_args()


if __name__ == '__main__':
    connector = ta.dialog_connector.DialogConnector(
        dialog_manager=ta.dialog_manager.FAQDialogManager('faq.yaml'),
        storage=ta.session_storage.BaseStorage()
    )
    server = ta.flask_server.FlaskServer(connector=connector)
    if args.poll:
        server.run_local_telegram()
    else:
        server.run_server()
