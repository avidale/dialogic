import tgalice

from tgalice.testing.testing_utils import make_context


DEFAULT_MESSAGE = 'this is the default message'


class CheckableFormFiller(tgalice.dialog_manager.form_filling.FormFillingDialogManager):
    SIGNS = {
        'jan': 'The Goat',
        'feb': 'The Water Bearer',
        'mar': 'The Fishes',
        'apr': 'The Ram',
        'may': 'The Bull',
        'jun': 'The Twins',
        'jul': 'The Crab',
        'aug': 'The Lion',
        'sep': 'The Virgin',
        'oct': 'The Balance',
        'nov': 'The Scorpion',
        'dec': 'The Archer',
    }

    def handle_completed_form(self, form, user_object, ctx):
        response = tgalice.dialog_manager.base.Response(
            text='Thank you, {}! Now we know: you are {} years old and you are probably {}. Lucky you!'.format(
                form['fields']['name'],
                2019 - int(form['fields']['year']),
                self.SIGNS[form['fields']['month']]
            )
        )
        return response


def test_form():
    dm = CheckableFormFiller(
        'tests/test_managers/form.yaml',
        default_message=DEFAULT_MESSAGE
    )
    resp = dm.respond(make_context(new_session=True))
    assert resp.text == DEFAULT_MESSAGE

    for q, a in [
        ('start the test', 'Please tell me your name'),
        ('Bob', 'Now tell me the year of your birth. Four digits, nothing more.'),
        ('not', 'Please try again. Your answer should be 4 digits.'),
        ('0', 'Please try again. Your answer should be 4 digits.'),
        ('1999', 'Wonderful! Now choose the month of your birth (the first 3 letters).'),
        ('lol', 'The answer should be one of the suggested options - the first 3 letters of a month.'),
        ('jan', 'That\'s great! Finally, tell me the date of your birth - one or two digits'),
        ('40', 'Please try again. Your answer should be a whole number - the day of your birth.'),
        ('02', 'Thank you, Bob! Now we know: you are 20 years old and you are probably The Goat. Lucky you!'),
        ('Okay, what\'s next?', DEFAULT_MESSAGE),
        ('But really', DEFAULT_MESSAGE)
    ]:
        resp = dm.respond(make_context(text=q, prev_response=resp))
        assert resp.text == a, 'expected "{}" to be responded by "{}", got "{}" instead'.format(q, a, resp.text)
