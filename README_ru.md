# dialogic
[![PyPI version](https://badge.fury.io/py/dialogic.svg)](https://badge.fury.io/py/dialogic)

[readme in english](https://github.com/avidale/dialogic/blob/master/README_en.md)

Это очередная обёртка на Python для навыков
[Алисы](https://yandex.ru/dev/dialogs/alice/doc/about.html) и 
[Салюта](https://salute.sber.ru/smartmarket/dev/) (Сбер) и ботов
в Telegram <sup>[*](#footnote1)</sup>, VK, и Facebook.

Она позволяет как быстро писать прототипы ботов для разных платформ, 
так и масштабировать их, когда кода и сценариев становится много.

Ранее пакет был известен как [tgalice](https://github.com/avidale/tgalice).

Установка [пакета](https://pypi.org/project/dialogic/): `pip install dialogic`

## Пример кода

Ниже описан бот, который на приветствие отвечает приветствием,
а на все остальные фразы - заглушкой по умолчанию.

```python
from dialogic.dialog_connector import DialogConnector
from dialogic.dialog_manager import TurnDialogManager
from dialogic.server.flask_server import FlaskServer
from dialogic.cascade import DialogTurn, Cascade

csc = Cascade()


@csc.add_handler(priority=10, regexp='(hello|hi|привет|здравствуй)')
def hello(turn: DialogTurn):
    turn.response_text = 'Привет! Это единственная условная ветка диалога.'


@csc.add_handler(priority=1)
def fallback(turn: DialogTurn):
    turn.response_text = 'Я вас не понял. Скажите мне "Привет"!'
    turn.suggests.append('привет')


dm = TurnDialogManager(cascade=csc)
connector = DialogConnector(dialog_manager=dm)
server = FlaskServer(connector=connector)

if __name__ == '__main__':
    server.parse_args_and_run()
```

Чтобы запустить приложение как веб-сервис, достаточно запустить данный скрипт.

Если приложение доступно по адресу `{BASE_URL}`, 
то вебхуки для Алисы, Салюта и Facebook будут доступны, соотвественно, 
на `{BASE_URL}/alice/`, `{BASE_URL}/salut/`, and `{BASE_URL}/fb/` 
(при желании, адреса можно изменить).
Вебхук для бота в Telegram будет установлен автоматически, 
если выставить в переменную окружения `TOKEN` значение, 
полученное от [@BotFather](https://t.me/BotFather).

Чтобы протестировать приложение локально, можно вызвать его с аргументами:
* `--cli` - диалог с ботом в командной строке, полностью онлайн
* `--poll` - запуск бота в Telegram в режиме long polling 
* `--ngrok` - локальный запуск с использованием 
  [ngrok](https://ngrok.com/) <sup>[**](#footnote2)</sup>, 
  чтобы создать туннель из вашего компьютера во внешний Интернет. 
  Удобный способ тестировать навыки Алисы.
  
## Больше возможностей

- Использование встроенных классификаторов интентов или сторонних средств NLU, 
  включая грамматики от Яндекса или любые доступные в Python модели.
- Подключение собственных поверхностей или настройка имеющихся.
- Логирование запросов и ответов для последующей аналитики.

Библиотека возможностей регулярно пополняется.

## Ресурсы и поддержка

В папе [examples](https://github.com/avidale/dialogic/tree/master/examples) 
собраны примеры использования компонент и запуска ботов.

Вопросы можно задать в чате 
[Dialogic.Digital support](https://t.me/joinchat/WOb48KC6I192zKZu) (Telegram).

<a id="footnote1">*</a> Обёртка для Telegram использует пакет 
[pyTelegramBotAPI](https://github.com/eternnoir/pyTelegramBotAPI).

<a id="footnote2">**</a> Обёртка для ngrok была взята из пакета
[flask-ngrok](https://github.com/gstaff/flask-ngrok).
