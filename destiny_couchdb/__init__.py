import asyncio
import functools
import os
import re
import sys

import httpx

from .client import Bungie
from .couchdb import CouchDB
from .manifest import get_manifest

_boundaries_finder = re.compile('(.)([A-Z][a-z]+)')
_boundaries_finder_2 = re.compile('([a-z0-9])([A-Z])')


@functools.cache
def camel_to_snake(txt):
    s1 = _boundaries_finder.sub(r'\1_\2', txt)
    return _boundaries_finder_2.sub(r'\1_\2', s1).lower()


@functools.cache
def dbname(txt):
    txt = camel_to_snake(txt)
    txt = txt.removeprefix('destiny_')
    txt = txt.removesuffix('_definition')
    return txt


async def sync_databases(couchdb, world):
    existing_dbs = set((await couchdb.get('/_all_dbs')).json())
    new_dbs = set(dbname(k) for k in world.keys())
    for db in (new_dbs - existing_dbs):
        await couchdb.put(f'/{db}')


# FIXME: Use bulk get/update APIs

async def sync_entity(couchdb, kind, entity):
    url = f"/{kind}/{entity['hash']}"
    print(url)
    try:
        old_doc = (await couchdb.get(url)).json()
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 404:
            old_doc = {}
        else:
            raise

    new_doc = old_doc | entity

    if new_doc != old_doc:
        await couchdb.put(url, params=new_doc.get('_rev', None), json=new_doc)


async def sync_manifest(couchdb, manifest):
    for kind, items in manifest.items():
        for hash, item in items.items():
            hash = int(hash)
            if 'hash' not in item:
                # For some reason, DetinyInventoryItemLite and maybe others don't have hashes
                item['hash'] = hash
            else:
                assert item['hash'] == hash, f"{kind=} {hash=} {item=}"
            await sync_entity(couchdb, dbname(kind), item)


async def main():
    async with (
            Bungie(os.environ['BUNGIE_KEY']) as bungo,
            CouchDB('http://localhost:5984', auth=('admin', 'admin')) as couchdb,
    ):
        mani = await get_manifest(bungo)
        world = await mani.get_world_json()
        await sync_databases(couchdb, world)
        await sync_manifest(couchdb, world)
