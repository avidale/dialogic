"""
Modified code from https://developers.google.com/sheets/api/quickstart/python
"""
import pickle
import os.path

from typing import List, Dict

from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request


# If modifying these scopes, delete the file token.pickle.


SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']

# The ID and range of a sample spreadsheet.
SAMPLE_SPREADSHEET_ID = '1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms'
SAMPLE_RANGE_NAME = 'Class Data!A2:E'


def creds_to_mongo(creds, collection, key='google_creds'):
    dump = pickle.dumps(creds)
    collection.update_one({'key': key}, {'$set': {'value': dump}}, upsert=True)


def creds_from_mongo(collection, key='google_creds'):
    one = collection.find_one({'key': key})
    if one:
        return pickle.loads(one['value'])


def update_google_creds(
        creds=None,
        client_config=None,
        client_config_filename='credentials.json',
        dump_token=False,
        pickle_path='token.pickle',
        scopes=SCOPES,
):
    """ Open the login page for the user """
    if not creds and os.path.exists(pickle_path):
        with open(pickle_path, 'rb') as token:
            creds = pickle.load(token)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if client_config is not None:
                flow = InstalledAppFlow.from_client_config(client_config, scopes)
            else:
                flow = InstalledAppFlow.from_client_secrets_file(client_config_filename, scopes)
            creds = flow.run_local_server(port=53021)
        # Save the credentials for the next run
        if dump_token:
            with open(pickle_path, 'wb') as token:
                pickle.dump(creds, token)
    return creds


def get_credentials():
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)

    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    return creds


def get_credentials_smart(collection):
    creds = creds_from_mongo(collection=collection)
    if not creds:
        print('Could not get Google credits from MongoDB')
        return
    creds = update_google_creds(
        creds=creds,
        client_config=(collection.find_one({'key': 'google_raw_creds'}) or {}).get('value'),
    )
    return creds


def load_sheet(creds=None, sheet_id=SAMPLE_SPREADSHEET_ID, range_name=SAMPLE_RANGE_NAME, rename=None) -> List[Dict]:
    """ Load sheet
    """
    if creds is None:
        creds = get_credentials()

    service = build('sheets', 'v4', credentials=creds, cache_discovery=False)

    # Call the Sheets API
    sheet = service.spreadsheets()
    result = sheet.values().get(spreadsheetId=sheet_id, range=range_name).execute()
    values = result.get('values', [])

    headers = values[0]
    if rename:
        headers = [rename.get(v, v) for v in headers]
    # resize each row to make the table rectangular
    for row in values[1:]:
        if len(row) < len(headers):
            row.extend([None] * (len(headers) - len(row)))
        if len(row) > len(headers):
            row[:] = row[:len(headers)]
    # fill the data
    data = []
    for row in values[1:]:
        data.append({
            header: value
            for header, value in zip(headers, row)
        })
    return data


if __name__ == '__main__':
    data = load_sheet()
    print(len(data), 'items loaded')
    print(data[0])
