import string
from typing import Optional
from urllib.parse import urljoin

import httpx

ROOT = 'https://www.bungie.net/Platform/'


class UrlFormatter(string.Formatter):
    """
    Does URL-safe path formatting.

    Automatically prepends the URL root.
    """

    def vformat(self, format, args, kwargs):
        txt = super().vformat(format, args, kwargs)
        if self.root:
            txt = urljoin(self.root, txt)
        return txt

    def __init__(self, root=ROOT):
        self.root = root


def path(url, /, *pargs, **kwargs):
    """
    Do a URL-safe path format.

    You almost certainly do not want a leading slash.
    """
    return UrlFormatter().vformat(url, pargs, kwargs)


class _HttpxBungieAuth:
    def __init__(self, token):
        self.token = token

    def __call__(self, request):
        request.headers['X-API-Key'] = self.token
        return request


def _check_status(response):
    response.raise_for_status()
    # The async client expects a coroutine, the sync client does not
    async def _(): pass
    return _()


DEFAULT_CLIENT_PARAMS = {
    'follow_redirects': True,
    # 'base_url': ROOT,
    'http2': True,
    # FIXME: Support merging this with user params
    'event_hooks': {
        'response': [_check_status]
    },
}


class Bungie:
    """
    Magic sync/async client factory.

    Should use ephemerally. Don't keep around.
    """
    # TODO: __slots__
    _sync: Optional[httpx.Client] = None
    _async: Optional[httpx.AsyncClient] = None

    token: str
    params: dict

    def __init__(self, token: str, /, **params):
        self.token = token
        self.params = DEFAULT_CLIENT_PARAMS | params

    def _make_client(self, cls: type):
        return cls(auth=_HttpxBungieAuth(self.token), **self.params)

    def __enter__(self) -> httpx.Client:
        if self._sync is None:
            self._sync = self._make_client(httpx.Client)
        return self._sync.__enter__()

    def __exit__(self, *exc):
        if self._sync is not None:
            self._sync.__exit__(*exc)

    async def __aenter__(self) -> httpx.AsyncClient:
        if self._async is None:
            self._async = self._make_client(httpx.AsyncClient)
        return await self._async.__aenter__()

    async def __aexit__(self, *exc):
        if self._async is not None:
            await self._async.__aexit__(*exc)


def parse_response(resp):
    blob = resp.json()
    assert blob['ErrorCode'] == 1, blob['ErrorStatus']
    return blob['Response']
