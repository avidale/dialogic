from dialogic.dialog_connector import DialogConnector
from dialogic.dialog_manager import TurnDialogManager
from dialogic.server.flask_server import FlaskServer
from dialogic.cascade import DialogTurn, Cascade

csc = Cascade()


@csc.add_handler(priority=10, regexp='(hello|hi|привет|здравствуй)')
def hello(turn: DialogTurn):
    turn.response_text = 'Hello! This is the only conditional phrase I have.'


@csc.add_handler(priority=1)
def fallback(turn: DialogTurn):
    turn.response_text = 'Hi! Sorry, I do not understand you.'
    turn.suggests.append('hello')


dm = TurnDialogManager(cascade=csc)
connector = DialogConnector(dialog_manager=dm)
server = FlaskServer(connector=connector)

if __name__ == '__main__':
    server.parse_args_and_run()
