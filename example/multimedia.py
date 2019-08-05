import re
import tgalice

MARINA_SONG_IN_ALICE = '<speaker audio="dialogs-upload/2067b0f4-0b8e-47d1-b264-d7f4dc572e4d/9a013d0b-6936-4b62-a18c-145b03acb84d.opus">'  # noqa
MARINA_SONG_IN_WEB = 'https://filebin.net/s0tbsdw97u6jz1u0/marina.mp3?t=ka8zlp2p'
IMAGE_ID_IN_ALICE = '213044/0c6463a2a6eb7f935034'
IMAGE_IN_WEB = 'https://i.pinimg.com/originals/43/94/ab/4394abfe9d1a8feeeedfccc41c0e9df2.gif'


class ExampleMediaDialogManager(tgalice.dialog_manager.BaseDialogManager):
    def respond(self, ctx):
        response = tgalice.dialog_manager.Response(text='please take it', user_object=ctx.user_object)
        has_context = False
        text = ctx.message_text.lower()
        if re.match('.*(image|picture).*', text):
            response.image_id = IMAGE_ID_IN_ALICE
            response.image_url = IMAGE_IN_WEB
            has_context = True
        if re.match('.*sound.*', text):
            has_context = True
            response.set_text(response.voice + '(only in alice) <speaker audio="alice-sounds-animals-elephant-1.opus">')
        if re.match('.*(music|sing|song).*', text):
            has_context = True
            response.set_text(response.voice + ' ' + MARINA_SONG_IN_ALICE)
            response.sound_url = MARINA_SONG_IN_WEB
        if not has_context:
            response.set_text('I can send a picture or make a sound.')
        response.suggests = ['send a picture', 'make a sound', 'play music']
        return response


if __name__ == '__main__':
    connector = tgalice.dialog_connector.DialogConnector(
        dialog_manager=ExampleMediaDialogManager(),
        storage=tgalice.session_storage.BaseStorage()
    )
    server = tgalice.flask_server.FlaskServer(connector=connector)
    server.parse_args_and_run()
