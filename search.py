"""
Look for the given documents
"""
import asyncio
import sys

from destiny_couchdb.couchdb import CouchDB


async def check_db(couch, db, item):
    try:
        await couch.get(f"/{db}/{item}")
    except Exception:
        pass
    else:
        return f"/{db}/{item}"


async def main():
    async with CouchDB('http://localhost:5984', auth=('admin', 'admin')) as couch:
        dbs = (await couch.get('/_all_dbs')).json()
        results = await asyncio.gather(*(
            check_db(couch, db, arg)
            for db in dbs
            for arg in sys.argv[1:]
        ))
        for result in results:
            if result:
                print(result)

asyncio.run(main())
