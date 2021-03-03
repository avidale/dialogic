import pytest

import dialogic.interfaces.yandex as yandex


@pytest.fixture
def example_response():
    result = {
      "response": {
        "text": "Здравствуйте! Это мы, хороводоведы.",
        "tts": "Здравствуйте! Это мы, хоров+одо в+еды.",
        "buttons": [
            {
                "title": "Надпись на кнопке",
                "payload": {},
                "url": "https://example.com/",
                "hide": True
            }
        ],
        "end_session": False
      },
      "version": "1.0"
    }
    return result


def test_deserialization(example_response):
    res = yandex.response.YandexResponse.from_dict(example_response)
    assert res.response.buttons[0].hide is True


def test_big_image():
    raw_resp = {
      "response": {
        "text": "Здравствуйте! Это мы, хороводоведы.",
        "tts": "Здравствуйте! Это мы, хоров+одо в+еды.",
        "card": {
          "type": "BigImage",
          "image_id": "1027858/46r960da47f60207e924",
          "title": "Заголовок для изображения",
          "description": "Описание изображения.",
          "button": {
            "text": "Надпись на кнопке",
            "url": "http://example.com/",
            "payload": {}
          }
        },
        "buttons": [
          {
            "title": "Надпись на кнопке",
            "payload": {},
            "url": "https://example.com/",
            "hide": True
          }
        ],
        "end_session": False
      },
      "version": "1.0"
    }
    resp = yandex.YandexResponse.from_dict(raw_resp)
    assert resp.response.card
    assert resp.response.card.type == yandex.response.CARD_TYPES.BIG_IMAGE
    assert resp.response.card.button.url == "http://example.com/"


def test_items_list():
    raw_resp = {
      "response": {
        "text": "Здравствуйте! Это мы, хороводоведы.",
        "tts": "Здравствуйте! Это мы, хоров+одо в+еды.",
        "card": {
          "type": "ItemsList",
          "header": {
            "text": "Заголовок галереи изображений",
          },
          "items": [
            {
              "image_id": "<image_id>",
              "title": "Заголовок для изображения.",
              "description": "Описание изображения.",
              "button": {
                "text": "Надпись на кнопке",
                "url": "http://example.com/",
                "payload": {}
              }
            }
          ],
          "footer": {
            "text": "Текст блока под изображением.",
            "button": {
              "text": "Надпись на кнопке",
              "url": "https://example.com/",
              "payload": {}
            }
          }
        },
        "buttons": [
          {
            "title": "Надпись на кнопке",
            "payload": {},
            "url": "https://example.com/",
            "hide": True
          }
        ],
        "end_session": False
      },
      "version": "1.0"
    }
    resp = yandex.YandexResponse.from_dict(raw_resp)
    assert resp.response.card
    assert resp.response.card.type == yandex.response.CARD_TYPES.ITEMS_LIST
    assert resp.response.card.header.text == 'Заголовок галереи изображений'
    assert resp.response.card.footer.button.text == 'Надпись на кнопке'
    assert resp.response.card.items[0].image_id == '<image_id>'
    assert resp.response.card.items[0].button.url == 'http://example.com/'
