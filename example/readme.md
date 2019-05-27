This example shows how to actually build a bot that can be deployed e.g. on Heroku.

- `faq.py` shows how to create a simple Q&A bot with a text-based config `faq.yaml`.
- `state.py` shows how you can create a custom dialog manager and track dialogue state (number of messages).

The file `requirements.txt` describes the packages required to run the bot (only `tgalice` in this example).

The file `Procfile` is needed only for Heroku: it shows what to run when your bot is deployed.

To run the bot locally (for Telegram only), you need to set an environment variable `TOKEN` 
to the token of your Telegram bot (given to you by t.me/botfather when you create a bot).

For example, to run the example `custom_manager.py` locally, you need to type in the command line (Windows)
```
cd <the directory with the examples>
set TOKEN=<your telegram token from @botfather>
python custom_manager.py --poll
```
(if you are not on Windows, you probably already know what to do).

To run the bot on the server (for both Alice and Telegram), you also need to set an environment variable `BASE_URL`
to the address of your application (such as `https://my-cool-app.herokuapp.com/`). 
After you deploy it, you can use the url `<BASE_URL>/alice/` as a webhook for an 
[Alice skill](https://tech.yandex.ru/dialogs/alice/).
