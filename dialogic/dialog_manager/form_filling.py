import re

from .base import CascadableDialogManager, Context, Response
from dialogic.nlu import basic_nlu, matchers
from dialogic.utils.configuration import load_config

from typing import List, Dict, Optional


class FieldOption:
    def __init__(self, data):
        self.text = None
        self.next = None  # name of the node to jump to if this option is chosen
        if isinstance(data, str):
            self.text = data
        else:
            self.text = data['text']
            self.next = data.get('next')

    @classmethod
    def from_data(cls, data):
        if data is None:
            return None
        return cls(data)


class FieldConfig:
    def __init__(self, obj, idx=-1):
        self.validate_regexp = re.compile(obj.get('validate_regexp', '.*'))
        self.id = idx
        self.name = obj.get('name', 'field_{}'.format(idx))
        self.question = obj.get('question') or obj.get('q')
        self.repeated_question = obj.get('repeated_question')
        assert self.question, f'The question should be non-empty, but it is absent in the form {obj}!'
        self.validate_message = obj.get('validate_message')
        self.options = [FieldOption(o) for o in (obj.get('options') or [])]
        self.multivalued = obj.get('multivalued') or False
        self.exit_option = FieldOption.from_data(obj.get('exit_option'))
        self.suggests = obj.get('suggests')
        self.next = obj.get('next')

        if self.options is not None:
            self.matcher = matchers.make_matcher(**obj.get('matching', {'key': 'levenshtein', 'threshold': 0.8}))
            self.matcher.fit(self.all_options_texts, self.all_options_texts)
        else:
            self.matcher = None

    @property
    def all_options(self) -> List[FieldOption]:
        if not self.options:
            return []
        result = self.options
        if self.exit_option:
            return result + [self.exit_option]
        return result

    @property
    def all_options_texts(self) -> List[str]:
        return [s.text for s in self.all_options]

    def update_value(self, text, old_value=None):
        if self.multivalued:
            if old_value is None:
                old_value = []
            return old_value[:] + [text]
        return text

    def get_next_name(self, response_text=None, matched_id=None) -> Optional[str]:
        if matched_id is None and response_text in self.all_options_texts:
            matched_id = self.all_options_texts.index(response_text)
        if matched_id is not None:
            o = self.all_options[matched_id]
            if o.next:
                return o.next
        if self.next:
            return self.next


class FormConfig:
    def __init__(self, config):
        self._cfg = load_config(config)
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

        self.fields: List[FieldConfig] = [FieldConfig(obj, idx=i) for i, obj in enumerate(self._cfg['fields'])]
        self.name2field: Dict[str, FieldConfig] = {c.name: c for c in self.fields}
        self.default_field = FieldConfig(self._cfg['default_field']) if 'default_field' in self._cfg else None
        self.num_fields = len(self.fields)


class FormFillingDialogManager(CascadableDialogManager):
    def __init__(self, config, *args, **kwargs):
        super(FormFillingDialogManager, self).__init__(*args, **kwargs)
        self.config = FormConfig(config)

    def try_to_respond(self, ctx: Context):
        user_object = ctx.user_object or {}
        normalized = basic_nlu.fast_normalize(ctx.message_text)
        form = user_object.get('forms', {}).get(self.config.form_name, {})
        form['name'] = self.config.form_name
        if form.get('is_active'):
            if self.config.exit_regexp and re.match(self.config.exit_regexp, normalized):
                form['is_active'] = False
                return Response(text=self.config.exit_message, user_object=user_object)
            question_id = form['next_question']
            validated_answer = self.validate_answer(form, ctx.message_text)
            if validated_answer is not None:
                q = self.config.fields[question_id]
                form['fields'][q.name] = q.update_value(text=validated_answer, old_value=form['fields'].get(q.name))
                next_question_id = question_id
                if not q.exit_option or q.exit_option.text == validated_answer:
                    next_question_id += 1
                next_name = q.get_next_name(response_text=validated_answer)
                if next_name:
                    next_question_id = self.config.name2field[next_name].id
                if next_question_id >= self.config.num_fields:
                    form.pop('next_question')
                    form['is_active'] = False
                    result = self.handle_completed_form(form, user_object, ctx)
                    if result is not None:
                        return result
                    return Response(text=self.config.finish_message, user_object=user_object)
                form['next_question'] = next_question_id
                return self.ask_question(next_question_id, user_object=user_object, reask=False, form=form)
            else:
                return self.ask_question(question_id, user_object=user_object, reask=True, form=form)
        elif re.match(self.config.start_regex, normalized):
            return self.start_dialogue(ctx)
        return None

    def start_dialogue(self, ctx: Context):
        """ Initialize the form, and say the intro or ask the first question.
        This function is taken out of try_to_respond, so that it could be triggered by some external factor.
        """
        user_object = ctx.user_object or {}
        if 'forms' not in user_object:
            user_object['forms'] = {}
        user_object['forms'][self.config.form_name] = {
            'fields': {},
            'is_active': True,
            'name': self.config.form_name,
            'next_question': -1
        }
        form = user_object['forms'][self.config.form_name]
        if self.config.start_message is not None:
            form['next_question'] = -1
            return Response(
                text=self.config.start_message, suggests=self.config.start_suggests, user_object=user_object
            )
        else:
            form['next_question'] = 0
            return self.ask_question(0, user_object, reask=False)

    def ask_question(self, next_question_id, user_object, reask=False, form=None):
        the_question = self.config.fields[next_question_id]
        form = form or {}
        fields = form.get('fields') or {}
        prev_value = fields.get(the_question.name)
        response = the_question.question
        if reask:
            if the_question.validate_message is not None:
                response = the_question.validate_message
            elif self.config.default_field and 'validate_message' in self.config.default_field:
                response = self.config.default_field['validate_message']
        options = the_question.all_options_texts
        if options:
            suggests = options[:]
            if the_question.multivalued and prev_value:
                suggests = [s for s in suggests if s not in prev_value]
                if the_question.repeated_question and not reask:
                    response = the_question.repeated_question
        elif the_question.suggests:
            suggests = the_question.suggests[:]
        else:
            suggests = []
        if self.config.exit_suggest is not None:
            suggests.append(self.config.exit_suggest)
        return Response(user_object=user_object, text=response, suggests=suggests)

    def validate_answer(self, form, message_text):
        question_id = form.get('next_question', -1)
        if question_id == -1:
            return message_text
        the_question = self.config.fields[question_id]
        normalized_text = basic_nlu.fast_normalize(message_text)
        if the_question.all_options:
            winner_label, best_score = the_question.matcher.match(message_text)
            return winner_label
        if the_question.validate_regexp is not None:
            if re.match(the_question.validate_regexp, normalized_text):
                return message_text
            else:
                return None
        return message_text

    def handle_completed_form(self, form, user_object, ctx):
        """ This method can be overwritten to do something useful.
        If it is not overwritten, then the dialog ends by the `finish_message` from config.
        If it is overwritten, then it should probably put the updated `user_object` argument into its Response.
        """
        return None
