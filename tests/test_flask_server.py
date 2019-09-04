import tgalice


def test_create_flask_server():
    server = tgalice.server.flask_server.FlaskServer(
        connector=tgalice.dialog_connector.DialogConnector(
            dialog_manager=tgalice.dialog_manager.BaseDialogManager()
        )
    )
