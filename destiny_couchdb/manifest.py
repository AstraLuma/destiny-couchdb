import contextlib
import tempfile
import zipfile

import aiosqlite

from .client import parse_response, path


class Manifest:
    def __init__(self, client, data):
        self._client = client
        self._data = data

    async def get_world_json(self, lang='en'):
        fragment = self._data['jsonWorldContentPaths'][lang]
        resp = await self._client.get(path(fragment))
        return resp.json()

    async def get_world_component(self, component, lang='en'):
        fragment = self._data['jsonWorldComponentContentPaths'][lang][component]
        resp = await self._client.get(path(fragment))
        return resp.json()

    @contextlib.asynccontextmanager
    async def _get_sqlite(self, url):
        """
        Downloads a database from bungie, extracts the zip, and hands it to sqlite
        """
        with tempfile.NamedTemporaryFile('w+b') as sqlf:
            with tempfile.TemporaryFile('w+b') as wrapperf:
                async with self._client.stream('GET', url) as response:
                    async for chunk in response.aiter_bytes():
                        wrapperf.write(chunk)

                wrapperf.seek(0)

                with zipfile.ZipFile(wrapperf) as zipf:
                    files = zipf.namelist()
                    assert len(files) == 1
                    with zipf.open(files[0]) as inner:
                        while chunk := inner.read(2**20):
                            sqlf.write(chunk)

            sqlf.flush()

            async with aiosqlite.connect(sqlf.name) as sql:
                sql.row_factory = aiosqlite.Row
                yield sql

    @contextlib.asynccontextmanager
    async def get_gear_database(self):
        for db in self._data['mobileGearAssetDataBases']:
            if db['version'] == 2:
                fragment = db['path']
                break
        else:
            raise RuntimeError("WTF Bungie")

        async with self._get_sqlite(path(fragment)) as sql:
            yield sql


async def get_manifest(client) -> Manifest:
    mani = parse_response(await client.get(path('Destiny2/Manifest/')))
    return Manifest(client, mani)
