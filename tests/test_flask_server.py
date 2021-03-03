import dialogic


def test_create_flask_server():
    server = dialogic.server.flask_server.FlaskServer(
        connector=dialogic.dialog_connector.DialogConnector(
            dialog_manager=dialogic.dialog_manager.BaseDialogManager()
        )
    )
