import typing
import dialogic
import logging

from dialogic.dialog import Context, Response
from models import VectorMatcher, respond_with_gpt

logging.basicConfig(level=logging.DEBUG)


class ChitChatDialogManager(dialogic.dialog_manager.CascadableDialogManager):
    def try_to_respond(self, ctx: Context) -> typing.Union[Response, None]:
        return Response(respond_with_gpt(ctx.message_text))


if __name__ == '__main__':
    manager = dialogic.dialog_manager.CascadeDialogManager(
        dialogic.dialog_manager.FAQDialogManager('faq.yaml', matcher=VectorMatcher()),
        ChitChatDialogManager()
    )
    connector = dialogic.dialog_connector.DialogConnector(
        dialog_manager=manager,
        storage=dialogic.storage.session_storage.BaseStorage()
    )
    server = dialogic.server.flask_server.FlaskServer(connector=connector)
    server.parse_args_and_run()
