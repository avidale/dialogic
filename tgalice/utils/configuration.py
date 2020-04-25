import json
import yaml

from collections import Iterable, Mapping


def load_config(config, accept_lists=False, accept_dicts=True):
    if isinstance(config, str):
        with open(config, 'r', encoding='utf-8') as f:
            if config.endswith('.json'):
                return json.load(f)
            else:
                return yaml.safe_load(f)
    elif isinstance(config, Iterable) and accept_lists:
        return config
    elif isinstance(config, Mapping) and accept_dicts:
        return config
    else:
        text = 'Config should be a json/yaml filename'
        if accept_lists:
            text = text + ' or a list'
        if accept_dicts:
            text = text + ' or a dict'
        text = text + ', got "{}" instead.'.format(type(config))
        raise ValueError(text)
