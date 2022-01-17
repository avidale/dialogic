import csv
import io
from typing import List, Dict

import requests
import http.client


def have_internet():
    """ See https://stackoverflow.com/a/29854274/6498293 """
    conn = http.client.HTTPSConnection("8.8.8.8", timeout=5)
    try:
        conn.request("HEAD", "/")
        return True
    except:
        return False
    finally:
        conn.close()


def gsheet_to_records(file_id, sheet_id):
    url = f'https://docs.google.com/spreadsheets/d/{file_id}/export?format=csv&id={file_id}&gid={sheet_id}'
    response = requests.get(url)
    response.encoding = response.apparent_encoding
    text = response.text
    return list(csv.DictReader(io.StringIO(text)))


def rename_dicts(list_of_dicts: List[Dict], rename: Dict):
    for item in list_of_dicts:
        for old_name, new_name in rename.items():
            if old_name in item:
                item[new_name] = item[old_name]
                del item[old_name]
    return list_of_dicts
