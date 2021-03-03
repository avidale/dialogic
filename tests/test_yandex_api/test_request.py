import pytest

import dialogic.interfaces.yandex as yandex


@pytest.fixture
def example_request():
    result = {
      "meta": {
        "locale": "ru-RU",
        "timezone": "Europe/Moscow",
        "client_id": "ru.yandex.searchplugin/5.80 (Samsung Galaxy; Android 4.4)",
        "interfaces": {
          "screen": {},
          "account_linking": {}
        }
      },
      "request": {
        "command": "закажи пиццу на улицу льва толстого 16 на завтра",
        "original_utterance": "закажи пиццу на улицу льва толстого, 16 на завтра",
        "type": "SimpleUtterance",
        "markup": {
          "dangerous_context": True
        },
        "payload": {},
        "nlu": {
          "tokens": [
            "закажи",
            "пиццу",
            "на",
            "льва",
            "толстого",
            "16",
            "на",
            "завтра"
          ],
          "entities": [
            {
              "tokens": {
                "start": 2,
                "end": 6
              },
              "type": "YANDEX.GEO",
              "value": {
                "house_number": "16",
                "street": "льва толстого"
              }
            },
            {
              "tokens": {
                "start": 3,
                "end": 5
              },
              "type": "YANDEX.FIO",
              "value": {
                "first_name": "лев",
                "last_name": "толстой"
              }
            },
            {
              "tokens": {
                "start": 5,
                "end": 6
              },
              "type": "YANDEX.NUMBER",
              "value": 16
            },
            {
              "tokens": {
                "start": 6,
                "end": 8
              },
              "type": "YANDEX.DATETIME",
              "value": {
                "day": 1,
                "day_is_relative": True
              }
            }
          ]
        }
      },
      "session": {
        "message_id": 0,
        "session_id": "2eac4854-fce721f3-b845abba-20d60",
        "skill_id": "3ad36498-f5rd-4079-a14b-788652932056",
        "user_id": "47C73714B580ED2469056E71081159529FFC676A4E5B059D629A819E857DC2F8",
        "user": {
          "user_id": "6C91DA5198D1758C6A9F63A7C5CDDF09359F683B13A18A151FBF4C8B092BB0C2",
          "access_token": "AgAAAAAB4vpbAAApoR1oaCd5yR6eiXSHqOGT8dT"
        },
        "application": {
          "application_id": "47C73714B580ED2469056E71081159529FFC676A4E5B059D629A819E857DC2F8"
        },
        "new": True,
      },
      "version": "1.0"
    }
    return result


def test_deserialization(example_request):
    req = yandex.request.YandexRequest.from_dict(example_request)
    assert 'пиццу' in req.request.command
    assert any(e.type == yandex.request.ENTITY_TYPES.YANDEX_FIO for e in req.request.nlu.entities)
    assert(any(e.tokens.end == 8 for e in req.request.nlu.entities))
    req_dict = req.to_dict()
    # todo: ignoring Nones,  assert req_dict == req


def test_intents():
    raw_req = {
        "command": "включи свет на кухне, пожалуйста",
        "nlu": {
            "intents": {
                "turn.on": {
                    "slots": {
                        "what": {
                            "type": "YANDEX.STRING",
                            "value": "свет"
                        },
                        "where": {
                            "type": "YANDEX.STRING",
                            "value": "на кухне"
                        }
                    }
                }
            }
        }
    }
    req = yandex.request.Request.from_dict(raw_req)
    assert "turn.on" in req.nlu.intents
    assert req.nlu.intents['turn.on'].slots['what'].type == "YANDEX.STRING"


def test_state_extraction():
    raw_req = {
      "meta": {
        "locale": "ru-RU",
        "timezone": "Europe/Moscow",
        "client_id": "ru.yandex.searchplugin/5.80 (Samsung Galaxy; Android 4.4)",
        "interfaces": {
          "screen": {}
        }
      },
      "request": {
        "command": "привет",
        "original_utterance": "привет",
        "type": "SimpleUtterance",
        "markup": {
          "dangerous_context": True
        },
        "payload": {},
        "nlu": {
          "tokens": [
             "привет"
          ],
          "entities": [
          ]
        }
      },
      "session": {
        "new": True,
        "message_id": 4,
        "session_id": "2eac4854-fce721f3-b845abba-20d60",
        "skill_id": "3ad36498-f5rd-4079-a14b-788652932056",
        "user_id": "AC9WC3DF6FCE052E45A4566A48E6B7193774B84814CE49A922E163B8B29881DC",
        "application": {
          "application_id": "AC9WC3DF6FCE052E45A4566A48E6B7193774B84814CE49A922E163B8B29881DC"
        },
      },
      "state": {
        "session": {
          "value": 10
        },
        "user": {
          "value": 42
        }
      },
      "version": "1.0"
    }
    req = yandex.YandexRequest.from_dict(raw_req)
    assert req.state.session and req.state.session['value'] == 10
    assert req.state.user and req.state.user['value'] == 42
