import json
import functools
import itertools
import os
import re

import httpx
import aioitertools

from .client import Bungie, path
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


async def sync_databases(couchdb, world, more=[]):
    existing_dbs = set((await couchdb.get('/_all_dbs')).json())
    new_dbs = set(dbname(k)
                  for k in itertools.chain(world.keys(), ('meta',), more))
    for db in (new_dbs - existing_dbs):
        await couchdb.put(f'/{db}')


# FIXME: Use bulk get/update APIs

async def patch_document(couchdb, url, data):
    try:
        old_doc = (await couchdb.get(url)).json()
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 404:
            old_doc = {}
        else:
            raise

    new_doc = old_doc | data

    if new_doc != old_doc:
        await couchdb.put(url, params=new_doc.get('_rev', None), json=new_doc)


async def sync_entity(couchdb, kind, entity):
    url = f"/{kind}/{entity['hash']}"
    print(url)
    await patch_document(couchdb, url, entity)


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


async def iter_tables(sql):
    async with sql.execute("SELECT * FROM sqlite_master WHERE type='table'") as cursor:
        async for row in cursor:
            yield row['name']


async def iter_table(sql, table):
    async with sql.execute(f"SELECT id, json FROM {table}") as cursor:
        async for row in cursor:
            data = json.loads(row['json'])
            hash = int.from_bytes(row['id'].to_bytes(4, signed=True))
            yield hash, data


async def update_metadata(couchdb, manifest):
    await patch_document(couchdb, '/meta/world', {
        'version': manifest['version']
    })
    await patch_document(couchdb, '/meta/gear_cdn', manifest['mobileGearCDN'])


async def update_gear(couchdb, bungie):
    prefix = (await couchdb.get('/meta/gear_cdn')).json()['Gear']
    all_docs = (await couchdb.get('/gear_assets/_all_docs', params={'include_docs': True})).json()

    gearfiles = {
        gfn
        for row in all_docs['rows']
        for gfn in row['doc']['gear']
    }

    dyes = {}
    for gf in gearfiles:
        hash = gf.removesuffix('.js')
        data = (await bungie.get(path(f"{prefix}/{gf}"))).json()
        data['hash'] = hash
        await sync_entity(couchdb, 'gear', data)

        for dye in itertools.chain(data['default_dyes'], data['locked_dyes'], data['custom_dyes']):
            if dye['hash'] in dyes:
                assert dye == dyes[dye['hash']
                                   ], f"old={dyes[dye['hash']]!r} new={dye!r}"
            dyes[dye['hash']] = dye

    for dye in dyes.values():
        await sync_entity(couchdb, 'dye_manifest', dye)


async def main():
    async with (
            Bungie(os.environ['BUNGIE_KEY']) as bungo,
            CouchDB('http://localhost:5984', auth=('admin', 'admin')) as couchdb,
    ):
        mani = await get_manifest(bungo)
        async with mani.get_gear_database() as gear:
            # Update from the world data
            world = await mani.get_world_json()
            tables = await aioitertools.list(iter_tables(gear))
            await sync_databases(couchdb, world, tables+['gear', 'dye_manifest'])
            # await sync_manifest(couchdb, world)
            await update_metadata(couchdb, mani._data)

            # Update from the gear data
            for table in tables:
                async for hash, entity in iter_table(gear, table):
                    entity['hash'] = hash
                    # await sync_entity(couchdb, dbname(table), entity)

            await update_gear(couchdb, bungo)
