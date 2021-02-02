from tgalice.nlg import reply_markup, controls


class Response:
    def __init__(self, text,
                 suggests=None, commands=None, voice=None, links=None,
                 image_id=None, image_url=None, sound_url=None,
                 gallery=None, image=None,
                 user_object=None, raw_response=None,
                 confidence=0.5, label=None,
                 rich_text=None,
                 show_item_meta=None,
                 ):
        self.text = text
        self.suggests = suggests or []
        self.commands = commands or []
        self.voice = voice if voice is not None else text
        self.links = links or []
        self.updated_user_object = user_object
        self.confidence = confidence
        self.image_id = image_id
        self.image_url = image_url  # todo: support them in Facebook as well
        self.sound_url = sound_url
        self.gallery = gallery
        assert self.gallery is None or isinstance(self.gallery, controls.Gallery)
        self.image = image
        assert self.image is None or isinstance(self.image, controls.BigImage)
        self.raw_response = raw_response
        self.label = label
        if rich_text:
            self.set_text(rich_text)
        self.show_item_meta = show_item_meta

    @property
    def user_object(self):
        # make it readonly, for clarity
        return self.updated_user_object

    def set_rich_text(self, rich_text):
        parser = reply_markup.TTSParser()
        try:
            parser.feed(rich_text)
        except ValueError as e:
            raise ValueError('Got error "{}" while parsing text "{}"'.format(e, rich_text))
        parser.close()
        self.text = parser.get_text()
        self.voice = parser.get_voice()
        self.links.extend(parser.get_links())
        return self

    def set_text(self, text_and_voice):
        # this method name is deprecated
        return self.set_rich_text(rich_text=text_and_voice)

    def add_link(self, title, url, hide=False):
        self.links.append({
            'title': title,
            'url': url,
            'hide': hide,
        })
