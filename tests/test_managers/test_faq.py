import tgalice

from tgalice.testing.testing_utils import make_context


DEFAULT_MESSAGE = 'this is the default message'


def test_faq():
    dm = tgalice.dialog_manager.FAQDialogManager(
        'tests/test_managers/faq.yaml',
        matcher='cosine',
        default_message=DEFAULT_MESSAGE
    )
    r1 = dm.respond(make_context(new_session=True))
    assert r1.text == DEFAULT_MESSAGE
    first_responses = {dm.respond(make_context(text='hi there', prev_response=r1)).text for i in range(30)}
    assert first_responses == {'Hello!', 'Nice to meet you!', 'Have a good time, human.'}

    r2 = dm.respond(make_context(text='hi there', prev_response=r1))
    assert set(r2.suggests) == {'How are you?', 'What can you do?'}

    r3 = dm.respond(make_context(text='how are you', prev_response=r2))
    assert r3.text == "I'm fine, thanks"

    r4 = dm.respond(make_context(text='What can you do?', prev_response=r3))
    assert r4.text == DEFAULT_MESSAGE
