
class SOURCES:
    ALICE = 'alice'
    FACEBOOK = 'facebook'
    TELEGRAM = 'telegram'
    TEXT = 'text'
    VK = 'vk'
    unknown_source_error_message = 'Source must be on of {"alice", "facebook", "telegram", "text", "vk"}'


class COMMANDS:
    EXIT = 'exit'


class REQUEST_TYPES:
    SIMPLE_UTTERANCE = 'SimpleUtterance'
    BUTTON_PRESSED = 'ButtonPressed'
