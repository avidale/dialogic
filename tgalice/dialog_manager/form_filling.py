import re
import yaml

from collections import Mapping
from tgalice.dialog_manager.base import CascadableDialogManager, Context
from tgalice.nlu import basic_nlu


class FieldConfig:
    def __init__(self, obj, idx=-1):
        self.validate_regexp = re.compile(obj.get('validate_regexp', '.*'))
        self.id = id
        self.name = obj.get('name', 'field_{}'.format(idx))
        self.question = obj['question']
        self.validate_message = obj.get('validate_message')
        self.options = obj.get('options')
        self.suggests = obj.get('suggests')


class FormConfig:
    def __init__(self, config):
        if isinstance(config, str):
            with open(config, 'r', encoding='utf-8') as f:
                self._cfg = yaml.load(f)
        elif isinstance(config, Mapping):
            self._cfg = config
        else:
            raise ValueError('Config should be a yaml filename or a dict')
        # todo: validate everything
        self.form_name = self._cfg['form_name']

        self.start_regex = re.compile(self._cfg['start'].get('regexp', '.*'))
        self.start_message = self._cfg['start'].get('message')
        self.start_suggests = self._cfg['start'].get('suggests', [])

        exit_block = self._cfg.get('exit', {})
        self.exit_regexp = re.compile(exit_block['regexp']) if 'regexp' in exit_block else None
        self.exit_message = exit_block.get('message')
        self.exit_suggest = exit_block.get('suggest')

        self.finish_message = self._cfg.get('finish', {}).get('message')

        self.fields = [FieldConfig(obj, idx=i) for i, obj in enumerate(self._cfg['fields'])]
        self.default_field = FieldConfig(self._cfg['default_field']) if 'default_field' in self._cfg else None
        self.num_fields = len(self.fields)


class FormFillingDialogManager(CascadableDialogManager):
    def __init__(self, config, *args, **kwargs):
        super(FormFillingDialogManager, self).__init__(*args, **kwargs)
        self.config = FormConfig(config)

    def try_to_respond(self, user_object, message_text, metadata):
        context = Context(user_object=user_object, message_text=message_text, metadata=metadata)
        normalized = basic_nlu.fast_normalize(message_text)
        form = user_object.get('forms', {}).get(self.config.form_name, {})
        if form.get('is_active'):
            if self.config.exit_regexp and re.match(self.config.exit_regexp, normalized):
                form['is_active'] = False
                return user_object, self.config.exit_message, [], []
            question_id = form['next_question']
            if self.answer_is_valid(form, message_text):
                form['fields'][self.config.fields[question_id].name] = message_text
                next_question_id = question_id + 1
                if next_question_id >= self.config.num_fields:
                    form['is_active'] = False
                    result = self.handle_completed_form(form, context)
                    if result is not None:
                        return result
                    return user_object, self.config.finish_message, [], []
                form['next_question'] = next_question_id
                return self.ask_question(next_question_id, user_object=user_object, reask=False)
            else:
                return self.ask_question(question_id, user_object=user_object, reask=True)
        elif re.match(self.config.start_regex, normalized):
            if 'forms' not in user_object:
                user_object['forms'] = {}
            # todo: if there is no start message, move directly to question 0
            user_object['forms'][self.config.form_name] = {
                'fields': {},
                'is_active': True,
                'next_question': -1
            }
            form = user_object['forms'][self.config.form_name]
            if self.config.start_message is not None:
                form['next_question'] = -1
                return user_object, self.config.start_message, self.config.start_suggests, []
            else:
                form['next_question'] = 0
                return self.ask_question(0, user_object, reask=False)
        return None

    def ask_question(self, next_question_id, user_object, reask=False):
        the_question = self.config.fields[next_question_id]
        response = the_question.question
        if reask:
            if the_question.validate_message is not None:
                response = the_question.validate_message
            elif 'validate_message' in self.config.default_field:
                response = self.config.default_field['validate_message']
        if the_question.options is not None:
            suggests = the_question.options
        elif the_question.suggests is not None:
            suggests = the_question.suggests
        else:
            suggests = []
        if self.config.exit_suggest is not None:
            suggests.append(self.config.exit_suggest)
        return user_object, response, suggests, []

    def answer_is_valid(self, form, message_text):
        question_id = form.get('next_question', -1)
        if question_id == -1:
            return True
        the_question = self.config.fields[question_id]
        if the_question.options is not None:
            return message_text in the_question.options
        if the_question.validate_regexp is not None:
            return re.match(the_question.validate_regexp, basic_nlu.fast_normalize(message_text))
        return True

    def handle_completed_form(self, form, context):
        pass
