import dialogic


if __name__ == '__main__':
    manager = dialogic.dialog_manager.CascadeDialogManager(
        dialogic.dialog_manager.AutomatonDialogManager('menu.yaml', matcher='cosine'),
        dialogic.dialog_manager.GreetAndHelpDialogManager(
            greeting_message="Дефолтное приветственное сообщение",
            help_message="Дефолтный вызов помощи",
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
