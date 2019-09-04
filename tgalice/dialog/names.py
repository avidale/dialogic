
class SOURCES:
    TELEGRAM = 'telegram'
    ALICE = 'alice'
    TEXT = 'text'
    FACEBOOK = 'facebook'
    unknown_source_error_message = 'Source must be on of {"telegram", "alice", "text", "facebook"}'


class COMMANDS:
    EXIT = 'exit'


class REQUEST_TYPES:
    SIMPLE_UTTERANCE = 'SimpleUtterance'
    BUTTON_PRESSED = 'ButtonPressed'
