import copy
import tgalice


SHOW_OBJECT_GALLERY = 'Объектная галерея'
SHOW_JSON_GALLERY = 'Галерея на json'
SHOW_JSON_TEXT = 'Текст на json'
SHOW_LOAD = 'Загрузка элементов'

SUGGESTS = [SHOW_JSON_GALLERY, SHOW_JSON_GALLERY, SHOW_JSON_TEXT, SHOW_LOAD]


class ControlsDialogManager(tgalice.dialog_manager.BaseDialogManager):
    def respond(self, ctx):
        response = tgalice.dialog_manager.Response('это текст по умолчанию')
        if ctx.message_text.lower() == SHOW_OBJECT_GALLERY.lower():
            response.gallery = tgalice.nlg.controls.Gallery(
                title='Большая галерея',
                items=[
                    tgalice.nlg.controls.GalleryItem(title='Первый элемент'),
                    tgalice.nlg.controls.GalleryItem(title='Второй элемент'),
                ],
                footer=tgalice.nlg.controls.GalleryFooter(text='Низ', button_payload={'нажал': 'подвал'})
            )
        elif ctx.message_text.lower() == SHOW_JSON_GALLERY.lower():
            response.raw_response = RAW_GALLERY
        elif ctx.message_text.lower() == SHOW_JSON_TEXT.lower():
            response.raw_response = RAW_TEXT
        elif ctx.message_text.lower() == SHOW_LOAD.lower():
            response.set_text('Вот тут ссыль <a href="https://example.com" hide=false>ссыль</a>')
        response.suggests.extend(SUGGESTS)
        return response


RAW_TEXT = {
    "text": "Здравствуйте! Это мы, хороводоведы.",
    "tts": "Здравствуйте! Это мы, хоров+одо в+еды.",
    "buttons": [
        {
            "title": "Скрываемая ссылка",
            "payload": {},
            "url": "https://example.com/",
            "hide": True
        },
        {
            "title": "Нескрываемая ссылка",
            "payload": {},
            "url": "https://example.com/",
            "hide": False
        },
        {
            "title": "Скрываемая нессылка",
            "payload": {},
            "hide": True
        },
        {
            "title": "Нескрываемая нессылка",
            "payload": {},
            "hide": False
        },
        {"title": SHOW_JSON_GALLERY},
        {"title": SHOW_OBJECT_GALLERY},
    ],
    "end_session": False
}


RAW_GALLERY = copy.deepcopy(RAW_TEXT)
RAW_GALLERY['card'] = {
    "type": "ItemsList",
    "header": {
        "text": "Заголовок галереи изображений",
    },
    "items": [
        {
            "image_id": "1030494/9409bc880f9d7a5d571b",
            "title": "Заголовок для изображения.",
            "description": "Описание изображения.",
            "button": {
                "text": "Надпись на кнопке",
                "url": "http://example.com/",
                "payload": {}
            }
        },
        {
            "image_id": "1030494/9409bc880f9d7a5d571b",
            "title": "Вторая картинка",
            "description": "Её описание.",
            "button": {
                "text": "Кнопка со ссылкой и лоадом",
                "url": "http://example.com/",
                "payload": {"key": "value"}
            }
        },
        {
            "title": "Текст без картинки и ссылки",
            "description": "Тут пэйлоад и текст кнопки",
            "button": {
                "text": "Кнопка со ссылкой и лоадом",
                "payload": {"key": "value"}
            }
        },
        {
            "title": "Текст без картинки и ссылки",
            "description": "Тут пэйлоад и кнопка без текста",
            "button": {
                "payload": {"key": "value"}
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
}

if __name__ == '__main__':
    connector = tgalice.dialog_connector.DialogConnector(
        dialog_manager=ControlsDialogManager(),
        storage=tgalice.storage.session_storage.BaseStorage()
    )
    server = tgalice.server.flask_server.FlaskServer(connector=connector)
    server.parse_args_and_run()
