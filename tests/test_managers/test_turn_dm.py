from dialogic.cascade import Cascade, DialogTurn
from dialogic.dialog_manager import TurnDialogManager
from dialogic.testing.testing_utils import make_context


def test_turn_dm():
    csc = Cascade()

    @csc.add_handler(priority=0)
    def fallback(turn: DialogTurn):
        turn.response_text = 'hi'

    @csc.add_handler(priority=1, intents=['shalom'])
    def fallback(turn: DialogTurn):
        turn.response_text = 'shalom my friend'

    dm = TurnDialogManager(cascade=csc, intents_file='tests/test_managers/intents.yaml')
    ctx = make_context('shalom')
    resp = dm.respond(ctx)
    assert resp.text == 'shalom my friend'
