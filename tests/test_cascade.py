import pytest
from dialogic.cascade import Cascade, DialogTurn
from dialogic.dialog import Context
from dialogic.testing.testing_utils import make_context

csc = Cascade()


@csc.add_handler(priority=0)
def t0(turn: DialogTurn):
    turn.response_text = '0'


@csc.add_handler(priority=1, intents=['i1'])
def t1(turn: DialogTurn):
    turn.response_text = '1'


@csc.add_handler(priority=1, intents=['i2'])
def t2(turn: DialogTurn):
    turn.response_text = '2'


@csc.add_handler(priority=2, intents=['i3'])
def t3(turn: DialogTurn):
    turn.response_text = '2'


@csc.add_handler(priority=3, stages=['s1'])
def t4(turn: DialogTurn):
    turn.response_text = 'stage 1'


@csc.postprocessor
def ask_for_tea(turn: DialogTurn):
    turn.response_text += '\nDo you want some tea?'


@pytest.mark.parametrize('intents,result', [
    ({}, 't0'),
    ({'i1': 1.0, 'i2': 0.5}, 't1'),
    ({'i2': 0.5}, 't2'),
    ({'i1': 1.0, 'i2': 0.5, 'i3': 0.1}, 't3'),
])
def test_ranking(intents, result):
    turn = DialogTurn(make_context(text='kek'), text='kek', intents=intents)
    assert csc(turn) == result


def test_ranking_stage():
    ctx = Context(message_text='kek', user_object={'stage': 's1'}, metadata=None)
    turn = DialogTurn(ctx, text='kek', intents={'i3': 1})
    assert turn.old_user_object == {'stage': 's1'}
    assert turn.stage == 's1'
    assert csc(turn) == 't4'


def test_postprocess():
    turn = DialogTurn(make_context(text='kek'), text='kek')
    turn.response_text = 'The weather is cool.'
    # without agenda, no postprocessors are called
    turn.release_control()
    csc.postprocess(turn)
    assert turn.response_text.endswith('cool.')
    # without control, no postprocessors are called
    turn.take_control()
    turn.add_agenda('ask_for_tea')
    csc.postprocess(turn)
    assert turn.response_text.endswith('cool.')
    # with control and agenda, postprocessors are called
    turn.release_control()
    csc.postprocess(turn)
    assert turn.response_text.endswith('tea?')
    # after postprocessing, agenda goes away
    assert not turn.agenda
