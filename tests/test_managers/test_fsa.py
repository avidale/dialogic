import pytest
import dialogic

from dialogic.dialog_manager.automaton import AutomatonDialogManager
from dialogic.testing.testing_utils import make_context


def test_empty_fsa():
    # FSA cannot be empty, because initial state must exist
    with pytest.raises(ValueError):
        fsa = AutomatonDialogManager(config={}, matcher='exact')


def test_minimal_fsa():
    cfg = {
        'states': {
            'first': {'a': 'hello'}
        }
    }
    fsa = AutomatonDialogManager(config=cfg, matcher='exact')
    assert len(fsa.states) == 2  # 'universal' state is always added but it never reached

    ctx = make_context(text='hi', new_session=True)
    resp = fsa.try_to_respond(ctx)
    assert resp.text == 'hello'


@pytest.fixture
def example_fsa():
    cfg = {
        'states': {
            'first': {'a': 'hello', 'next': [{'intent': 'time', 'label': 'second'}]},
            'second': {'a': '8 pm'},
            'third': {'q': ['help', 'what can you do'], 'a': 'I am always here to help'},
            'fourth': {'a': 'hello again', 'next': [{'intent': 'time', 'label': 'second'}]},
            'fifth': {'q': ['thanks'], 'a': 'thank you', 'restore_prev_state': True},
            'intro': {'q': ['let\'s introduce ourselves'], 'a': 'I am Max. And you?', 'default_next': 'my_name'},
            'my_name': {'a': 'Nice to meet you'},
        },
        'intents': {
            'time': {'regex': '.*time.*'}
        },
        'options': {
            'state_on_new_session': 'fourth',
        },
    }
    fsa = AutomatonDialogManager(config=cfg, matcher='exact')
    return fsa


def test_basic_transition(example_fsa):
    fsa: AutomatonDialogManager = example_fsa

    # initialize
    ctx0 = make_context(text='hi', new_session=True)
    resp0 = fsa.try_to_respond(ctx0)
    assert resp0.text == 'hello'

    # successful transition
    ctx1 = make_context(text='can you tell me the time please', prev_response=resp0)
    resp1 = fsa.try_to_respond(ctx1)
    assert resp1.text == '8 pm'

    # the same transition from another state is not allowed
    ctx2 = make_context(text='can you tell me the time please', prev_response=resp1)
    resp2 = fsa.try_to_respond(ctx2)
    assert not resp2

    # failed transition: text was not matched
    ctx1 = make_context(text='you will not understand me', prev_response=resp0)
    resp1 = fsa.try_to_respond(ctx1)
    assert not resp1

    # transition from the universal state
    ctx1 = make_context(text='help', prev_response=resp0)
    resp1 = fsa.try_to_respond(ctx1)
    assert resp1.text == 'I am always here to help'

    # new session
    ctx2 = make_context(new_session=True, prev_response=resp1)
    resp2 = fsa.try_to_respond(ctx2)
    assert resp2.text == 'hello again'

    # after transient state, context is restored and previous transition is possible
    ctx3 = make_context(prev_response=resp2, text='thanks')
    resp3 = fsa.try_to_respond(ctx3)
    assert resp3.text == 'thank you'
    ctx4 = make_context(prev_response=resp3, text='tell me time now')
    resp4 = fsa.try_to_respond(ctx4)
    assert resp4.text == '8 pm'


def test_default_transition(example_fsa):
    fsa: AutomatonDialogManager = example_fsa

    ctx0 = make_context(text='hi', new_session=True)
    resp0 = fsa.try_to_respond(ctx0)

    ctx1 = make_context('let\'s introduce ourselves', prev_response=resp0)
    resp1 = fsa.try_to_respond(ctx1)

    ctx2 = make_context('Stasy', prev_response=resp1)
    resp2 = fsa.try_to_respond(ctx2)
    assert resp2.text == 'Nice to meet you'
