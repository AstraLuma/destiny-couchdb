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


async def get_manifest(client) -> Manifest:
    mani = parse_response(await client.get(path('Destiny2/Manifest/')))
    return Manifest(client, mani)
