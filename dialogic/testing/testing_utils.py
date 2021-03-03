from dialogic.dialog_manager import Context


def make_context(text='', prev_response=None, new_session=False):
    if prev_response is not None:
        user_object = prev_response.updated_user_object
    else:
        user_object = {}
    if new_session:
        metadata = {'new_session': True}
    else:
        metadata = {}
    return Context(user_object=user_object, metadata=metadata, message_text=text)
