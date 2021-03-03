import json
import dialogic

HELP_MESSAGE = 'Hi! This is a math test chat. Say "Start test" to start the test.'


def handle_full_form(form, user_object, ctx):
    return dialogic.dialog_manager.Response(
        "That's all. Thank you!\nYour form is \n{}\n and it will be graded soon".format(
            json.dumps(form['fields'], indent=2)
        ),
        user_object=user_object
    )


if __name__ == '__main__':
    connector = dialogic.dialog_connector.DialogConnector(
        dialog_manager=dialogic.dialog_manager.FormFillingDialogManager('form.yaml', default_message=HELP_MESSAGE),
        storage=dialogic.storage.session_storage.BaseStorage()
    )
    connector.dialog_manager.handle_completed_form = handle_full_form
    server = dialogic.server.flask_server.FlaskServer(connector=connector)
    server.parse_args_and_run()
