# dialogic
[![PyPI version](https://badge.fury.io/py/dialogic.svg)](https://badge.fury.io/py/dialogic)

This is yet another common Python wrapper for 
[Alice](https://yandex.ru/dev/dialogs/alice/doc/about.html) and 
[Sber Salut](https://salute.sber.ru/smartmarket/dev/) skills 
and bots in Telegram<sup>[*](#footnote1)</sup>, VK, 
and Facebook Messenger.

Currently, it provides:
- An (almost) unified interface between your bot 
  and Alice/SalutTelegram/Facebook/VK: `DialogConnector`,
  for which you can create or customize adapters.
- A number of simple dialogue constructors: `BaseDialogManager` and its flavors, including:
    - a simple FAQ dialog manager
    - a simple form-filling dialog manager
    - a flexible finite state automaton dialog manager
    - an even more flexible turn-based dialog manager
- A wrapper for storing dialogue state: `BaseStorage` and its flavors (specifially, `MongoBasedStorage`)
- Yet another wrapper for serving your bot as a Flask application

This [package](https://pypi.org/project/dialogic/) may be installed with `pip install dialogic`.

### A brief how-to

To create your own bot, you need either to write a config for an existing dialog manager, 
or to inherit your own dialog manager from `BaseDialogManager`. 

The components of `dialogic` may be combined into a working app as follows:

```python
import dialogic

class EchoDialogManager(dialogic.dialog_manager.BaseDialogManager):
    def respond(self, ctx: dialogic.dialog.Context):
        return dialogic.dialog.Response(text=ctx.message_text)

connector = dialogic.dialog_connector.DialogConnector(
    dialog_manager=EchoDialogManager(), 
    storage=dialogic.session_storage.BaseStorage()
)
server = dialogic.flask_server.FlaskServer(connector=connector)

if __name__ == '__main__':
    server.parse_args_and_run()
```
Now, if your app is hosted on address `{BASE_URL}`, 
then webhooks for Alice, Salut and Facebook will be available, 
respectively, at `{BASE_URL}/alice/`, `{BASE_URL}/salut/`, and `{BASE_URL}/fb/` (and you can reconfigure it, if you want). 
The webhook for Telegram will be set automatically, if you set the `TOKEN` environment variable to the token 
given to you by the [@BotFather](https://t.me/BotFather).

If you want to test your app locally, you can run it with command line args:
* `--cli` - to read and type messages in command line, completely offline
* `--poll` - to run a Telegram bot locally, in long polling mode (in some countries, you need a VPN to do this)
* `--ngrok` - to run the bot locally, using the [ngrok](https://ngrok.com/) tool<sup>[**](#footnote2)</sup> 
to create a tunnel from your machine into the internet. This is probably the simplest way to test Alice skills 
without deploying them anywhere .

The [examples](https://github.com/avidale/dialogic/tree/master/examples) directory contains more detailed examples 
of how to create dialogs and serve the bot. 

If you have questions, you can ask them in the Telegram chat 
[Dialogic.Digital support](https://t.me/joinchat/WOb48KC6I192zKZu).

<a id="footnote1">*</a> The Telegram wrapper is based on the 
[pyTelegramBotAPI](https://github.com/eternnoir/pyTelegramBotAPI) package.

<a id="footnote2">**</a> The ngrok connector was taken from the
[flask-ngrok](https://github.com/gstaff/flask-ngrok) library. It will be refactored to a dependency, 
as soon as the library is updated on PyPI.
