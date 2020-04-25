import tgalice


if __name__ == '__main__':
    manager = tgalice.dialog_manager.CascadeDialogManager(
        tgalice.dialog_manager.AutomatonDialogManager('menu.yaml', matcher='cosine'),
        tgalice.dialog_manager.GreetAndHelpDialogManager(
            greeting_message="Дефолтное приветственное сообщение",
            help_message="Дефолтный вызов помощи",
            default_message='Я вас не понимаю.',
            exit_message='Всего доброго! Было приятно с вами пообщаться!'
        )
    )
    connector = tgalice.dialog_connector.DialogConnector(
        dialog_manager=manager,
        storage=tgalice.storage.session_storage.BaseStorage()
    )
    server = tgalice.server.flask_server.FlaskServer(connector=connector)
    server.parse_args_and_run()
