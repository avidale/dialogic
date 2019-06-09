# tgalice
This is yet another common Python wrapper for Telegram bots<sup>[*](#footnote1)</sup> and Alice skills.

Currently, it provides:
- An (almost) unified interface between your bot and Telegram or Alice: `DialogConnector`
- A number of simple dialogue constructors: `BaseDialogManager` and its flavors
- A wrapper for storing dialogue state: `BaseStorage` and its flavors

This [package](https://pypi.org/project/tgalice/) may be installed with 
```
pip install tgalice
```

The three components of `tgalice` may be combined as follows:
```python
import tgalice
connector = tgalice.dialog_connector.DialogConnector(
    dialog_manager=tgalice.dialog_manager.BaseDialogManager(), 
    storage=tgalice.session_storage.BaseStorage()
)
```
Now you can plug both Alice and Telegram into the connector. In the example below, they are served with Flask. 
```python
@app.route("/" + ALICE_URL, methods=['POST'])
def alice_response():
    response = connector.respond(request.json, source='alice')
    return json.dumps(response, ensure_ascii=False, indent=2)


@bot.message_handler(func=lambda message: True)
def telegram_response(message):
    response = connector.respond(message, source='telegram')
    bot.reply_to(message, **response)
```

To reduce the amount of boilerplate code even more, you can use the `FlaskServer` class, 
which configures both Alice and Telegram for you, and can also run in pure command line mode 
(e.g. if you want to test your bot without internet connection).
```python
server = tgalice.flask_server.FlaskServer(connector=connector)
server.parse_args_and_run()
```

The [examples](https://github.com/avidale/tgalice/tree/master/example) directory contains more detailed examples 
of how to create dialogs and serve the bot. 

<a id="footnote1">*</a> The Telegram wrapper is based on the [pyTelegramBotAPI](https://github.com/eternnoir/pyTelegramBotAPI) 
package. 