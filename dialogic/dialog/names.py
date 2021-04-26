
class SOURCES:
    ALICE = 'alice'
    FACEBOOK = 'facebook'
    SALUT = 'salut'
    TELEGRAM = 'telegram'
    TEXT = 'text'
    VK = 'vk'
    unknown_source_error_message = 'Source must be on of {"alice", "facebook", "telegram", "text", "vk"}'


class COMMANDS:
    EXIT = 'exit'
    REQUEST_GEOLOCATION = 'request_geolocation'


class REQUEST_TYPES:
    SIMPLE_UTTERANCE = 'SimpleUtterance'
    PUSH = 'push'
    BUTTON_PRESSED = 'ButtonPressed'
    SHOW_PULL = 'Show.Pull'
    GEOLOCATION_ALLOWED = 'Geolocation.Allowed'
    GEOLOCATION_REJECTED = 'Geolocation.Rejected'
