"""
Grab the Destiny 2 manifest and show it in a user-sensible way.
"""
import os
from pprint import pprint

from destiny_couchdb.client import Bungie, path

with Bungie(os.environ['BUNGIE_KEY']) as client:
    resp = client.get(path('Destiny2/Manifest/'))
    blob = resp.json()
    assert blob['ErrorCode'] == 1, blob['ErrorStatus']
    data = blob['Response']

    for category, contents in data.items():
        print(category)
        if not contents:
            print(f"\t(Empty {type(contents).__name__})")
        elif isinstance(contents, str):
            print(f"\t{contents!r}")
        elif isinstance(contents, list):
            for item in contents:
                print(f"\t{item!r}")
        elif isinstance(contents, dict):
            if category == 'mobileGearCDN':
                for k, v in contents.items():
                    print(f"\t{k}: {v!r}")
            elif 'en' in contents:
                lang = contents['en']
                if isinstance(lang, str):
                    print(f"\tEN: {lang!r}")
                elif isinstance(lang, dict):
                    for k, v in contents['en'].items():
                        print(f"\tEN:{k}: {v!r}")
                else:
                    print(f"\tEN:{lang!r}")
            else:
                print(f"\t{contents.keys()}")
        else:
            print(f"\t{type(contents)}")
