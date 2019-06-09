import tgalice

HELP_MESSAGE = 'Hi! This is a math test chat. Say "Start test" to start the test.'

if __name__ == '__main__':
    connector = tgalice.dialog_connector.DialogConnector(
        dialog_manager=tgalice.dialog_manager.FormFillingDialogManager('form.yaml', default_message=HELP_MESSAGE),
        storage=tgalice.session_storage.BaseStorage()
    )
    server = tgalice.flask_server.FlaskServer(connector=connector)
    server.parse_args_and_run()
