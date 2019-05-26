This example shows how to actually build a bot that can be deployed (e.g. on Heroku).

The file `main.py` describes the technical details of deploying the bot: what 

The file `logic.py` shows how the dialogue is actually managed.

The file `requirements.txt` describes the packages required to run the bot (only `tgalice` in this example).

The file `Procfile` is needed only for Heroku: it shows what to run when your bot is deployed.

To run the bot locally (for Telegram only), you need to set an environment variable `TOKEN` 
to the token of your Telegram bot (given to you by t.me/botfather when you create a bot).

To run the bot on the server (for both Alice and Telegram), you also need to set an environment variable `BASE_URL`
to the address of your application (such as `https://my-cool-app.herokuapp.com/`).