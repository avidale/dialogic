import distutils.util
import warnings

from html.parser import HTMLParser


class TTSParser(HTMLParser):
    """
    Allows parsing texts like
        'I study in the <text>1</text><voice>first</voice> grade. <a href="blood5.ru">The proof</a>'
    """
    TAG_TEXT = 'text'
    TAG_VOICE = 'voice'
    TAG_LINK = 'a'
    TAG_SPEAKER = 'speaker'  # it has no close tag
    TAG_IMG = 'img'
    SUPPORTED_TAGS = {TAG_TEXT, TAG_VOICE, TAG_LINK, TAG_SPEAKER, TAG_IMG}

    def __init__(self):
        super(TTSParser, self).__init__()
        self._text = ''
        self._voice = ''
        self._current_tag = None
        self._links = []
        self._image_id = None
        self._image_url = None

    def handle_starttag(self, tag, attrs):
        if self._current_tag is not None:
            raise ValueError('Open tag "{}" encountered, but tag "{}" is not closed'.format(self._current_tag, tag))
        attrs_dict = dict(attrs) if attrs else {}
        if tag not in self.SUPPORTED_TAGS:
            warnings.warn('Encountered an unknown tag "{}", will ignore it'.format(tag))
        if tag == self.TAG_SPEAKER:
            self._voice += self.get_starttag_text()
            return  # speaker tag cannot be current
        self._current_tag = tag
        if tag == self.TAG_LINK:
            if 'href' not in attrs_dict:
                raise ValueError('The "a" tag has no "href" attribute; attrs: "{}".'.format(attrs))
            link = {'url': attrs_dict['href'], 'title': ''}
            if 'hide' in attrs_dict:
                link['hide'] = bool(distutils.util.strtobool(attrs_dict['hide']))
            self._links.append(link)
        if tag == self.TAG_IMG:
            self._image_id = attrs_dict.get('id')
            self._image_url = attrs_dict.get('src')

    def handle_endtag(self, tag):
        if self._current_tag is None:
            raise ValueError('Encountered close tag "{}", but there are no open tags'.format(tag))
        if tag == self.TAG_LINK:
            if self._links[-1]['title'].strip() == '':
                raise ValueError('The "a" tag has emtpy contents')
        self._current_tag = None

    def handle_data(self, data):
        if self._current_tag is None or self._current_tag == self.TAG_TEXT:
            self._text += data
        if self._current_tag is None or self._current_tag == self.TAG_VOICE:
            self._voice += data
        if self._current_tag == self.TAG_LINK:
            self._links[-1]['title'] += data

    def get_text(self):
        return self._text

    def get_voice(self):
        return self._voice

    def get_links(self):
        return self._links

    def get_image_id(self):
        return self._image_id

    def get_image_url(self):
        return self._image_url
