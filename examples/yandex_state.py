"""
This file illustrates several techniques:
- how to store user object (session + user) in Alice
- how to extract intents from Yandex native NLU
"""

import dialogic


class ExampleDialogManager(dialogic.dialog_manager.BaseDialogManager):
    def respond(self, ctx):
        if ctx.source != dialogic.SOURCES.ALICE:
            return dialogic.dialog.Response('Простите, но я работаю только в Алисе.')
        suggests = ['меня зовут иван', 'как меня зовут', 'сколько было сессий', 'повтори']
        uo = ctx.user_object
        if 'user' not in uo:
            uo['user'] = {}
        if 'session' not in uo:
            uo['session'] = {}

        intents = ctx.yandex.request.nlu.intents
        if ctx.session_is_new():
            uo['user']['sessions'] = uo['user'].get('sessions', 0) + 1
            text = 'Привет! Вы находитесь в тестовом навыке. Чтобы выйти, скажите "Алиса, хватит".'
        elif 'set_name' in intents:
            name = intents['set_name'].slots['name'].value
            text = 'Запомнила, вас зовут {}'.format(name)
            uo['user']['name'] = name
        elif 'get_name' in intents:
            if uo['user'].get('name'):
                text = 'Кажется, ваше имя {}'.format(uo['user']['name'])
            else:
                text = 'Я не помню, как вас зовут. Пожалуйста, представьтесь.'
        elif 'YANDEX.REPEAT' in intents:
            if 'last_phrase' in uo['session']:
                text = uo['session']['last_phrase']
            else:
                text = 'Не помню, о чем мы говорили'
        else:
            text = 'У нас с вами было уже {} разговоров!'.format(uo['user'].get('sessions', 0))

        uo['session']['last_phrase'] = text
        return dialogic.dialog_manager.Response(user_object=uo, text=text, suggests=suggests)


if __name__ == '__main__':
    connector = dialogic.dialog_connector.DialogConnector(
        dialog_manager=ExampleDialogManager(),
        alice_native_state=True,
    )
    server = dialogic.server.flask_server.FlaskServer(connector=connector)
    server.parse_args_and_run()
