import tgalice

from tgalice.dialog.phrase import Phrase


def test_phrase_from_string():
    p1 = Phrase.from_object('hello')
    assert p1.texts == ['hello']
    resp = p1.render()
    assert resp.text == resp.voice == 'hello'

    p2 = Phrase.from_object('<text>Ciao</text><voice>Чао</voice>')
    resp = p2.render()
    assert resp.text == 'Ciao'
    assert resp.voice == 'Чао'


def test_phrase_from_dict():
    p1 = Phrase.from_object({
        'name': 'greeting',
        'text': 'hello',
        'exit': True,
        'suggests': ['Ciao', 'Bye'],
    })
    resp = p1.render(additional_suggests=['Auf Wiedersehen'])
    assert resp.commands == [tgalice.dialog.names.COMMANDS.EXIT]
    assert resp.suggests == ['Ciao', 'Bye', 'Auf Wiedersehen']


def test_random_phrase():
    p1 = Phrase(name='hi', text=['hello', 'hi'])

    assert len({p1.render(seed=1).text for i in range(100)}) == 1
    assert len({p1.render().text for i in range(100)}) == 2
