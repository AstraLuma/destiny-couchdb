import os
from pprint import pprint

from destiny_couchdb.client import Client, path

with Client(os.environ['BUNGIE_KEY']) as client:
    resp = client.get(path('Destiny2/Manifest/'))
    blob = resp.json()
    assert blob['ErrorCode'] == 1, blob['ErrorStatus']
    data = blob['Response']

    resp = client.head(path(data['mobileGearCDN']['Gear']))
    print(resp.headers)
