from typing import Dict

from . import request, response
from .request import YandexRequest
from .response import YandexResponse


def extract_yandex_forms(req: YandexRequest) -> Dict[str, Dict[str, str]]:
    results = {}
    raw_forms = req and req.request and req.request.nlu and req.request.nlu.intents
    if not raw_forms:
        return results
    for intent_name, intent in raw_forms.items():
        results[intent_name] = {
            slot_name: slot.value
            for slot_name, slot in intent.slots.items()
        }
    return results
