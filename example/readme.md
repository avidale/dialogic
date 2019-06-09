This example shows how to actually build a bot that can be deployed e.g. on Heroku.

#### About the contents

- `faq.py` shows how to create a simple Q&A bot with a text-based config `faq.yaml`.
- `state.py` shows how you can create a custom dialog manager and track dialogue state (number of messages).
- `form.py` shows how to configure a sequence of questions.

The file `requirements.txt` describes the packages required to run the bot 
(only `tgalice` and `flask` in this example).

The file `Procfile` is needed only for Heroku: it shows what to run when your bot is deployed.

#### Deploy in command line mode
To run the bot locally (in the command line mode, without Internet connection) you need no specific setup, 
except installing the requirements (`pip install -r requirements.txt`, if you don't have them yet).
The argument `--cli` enables command line mode. 

For example, to run the example `faq.py` in the command line mode, you need to type in the command line (Windows)
```
cd <the directory with the examples>
python faq.py --cli
```

#### Local deploy for Telegram
To run the bot in the polling mode (for Telegram only), you need to set an environment variable `TOKEN` 
to the token of your Telegram bot (given to you by t.me/botfather when you create a bot).

For example, to run the example `faq.py` locally for Telegram, you need to type in the command line (Windows)
```
cd <the directory with the examples>
set TOKEN=<your telegram token from @botfather>
python faq.py --poll
```
(if you are not on Windows, you probably already know what to do).

#### Web deploy
To run the bot on the server (for both Alice and Telegram), you need to set the token 
and the environment variable `BASE_URL`
to the address of your application (such as `https://my-cool-app.herokuapp.com/`). 
After you deploy it, you can use the url `<BASE_URL>/alice/` as a webhook for an 
[Alice skill](https://tech.yandex.ru/dialogs/alice/).
