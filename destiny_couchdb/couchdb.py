from typing import Optional

import httpx


def _check_status(response: httpx.Response):
    response.raise_for_status()
    # The async client expects a coroutine, the sync client does not
    async def _(): pass
    return _()


DEFAULT_CLIENT_PARAMS = {
    'follow_redirects': True,
    'http2': True,
    'headers': {'Accept': 'application/json'},
    # FIXME: Support merging this with user params
    'event_hooks': {
        'response': [_check_status]
    },
}


class CookieAuth(httpx.Auth):
    """
    Implement CouchDB Cookie authentication
    """
    # requires_response_body = True

    def __init__(self, user, password):
        self._creds = user, password

    def auth_flow(self, request):
        resp = yield request
        if resp.status_code == 401:
            # (re)authenticate with the server
            user, pw = self._creds
            resp = yield httpx.Request(
                'POST', request.url.join('/_session'),
                json={'name': user, 'password': pw},
            )
            resp.raise_for_status()
            # assert resp.json()['ok']

            # re-issue the request
            yield request


class CouchDB:
    """
    Magic sync/async client factory.

    Should use ephemerally. Don't keep around.
    """
    # TODO: __slots__
    _sync: Optional[httpx.Client] = None
    _async: Optional[httpx.AsyncClient] = None

    params: dict

    def __init__(self, server: str, /, **params):
        self.params = DEFAULT_CLIENT_PARAMS | \
            {'base_url': server} | \
            params

    def _make_client(self, cls: type):
        return cls(**self.params)

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
