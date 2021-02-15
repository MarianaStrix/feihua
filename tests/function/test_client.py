import json
from asyncio import TimeoutError
from http import HTTPStatus
from unittest import mock

import pytest
from aiohttp.client_exceptions import ClientConnectionError
from aiohttp.test_utils import make_mocked_coro
from yarl import URL

from feihua.exceptions import ClientError
from feihua.utils import _AsyncCM
from tests.identical import identical


class MockResponse:
    def __init__(self, json, status, headers, read=None):
        self._json = json
        self.status = status
        self.headers = headers
        self._read = read

    async def json(self, **kwargs):
        return self._json

    async def read(self, **kwargs):
        return json.dumps(self._json).encode()

    def close(self):
        pass

    async def __aexit__(self, exc_type, exc, tb):
        pass

    async def __aenter__(self):
        return self


@pytest.mark.parametrize(
    "api_version, path, query, url",
    [
        ("/v1", "/zone", "a=2", URL("https://dns.zone.ru/v1/zone?a=2")),
        ("/v1", "/zone", {"a": 2}, URL("https://dns.zone.ru/v1/zone?a=2")),
        ("/v2", "/zone/", None, URL("https://dns.zone.ru/v2/zone/")),
        ("/v2/", "/zone", None, URL("https://dns.zone.ru/v2//zone")),
    ],
)
@pytest.mark.asyncio
async def test_canonicalize_url(client, api_version, path, query, url):
    assert client._canonicalize_url(api_version, path, query) == url


@pytest.mark.asyncio
async def test_query_json(client, data_recordsets_function):
    expected_data = data_recordsets_function["data_single_recordset"]
    expected_status = HTTPStatus.OK
    with mock.patch("feihua.client.Client._query") as mock_query:
        res = MockResponse(expected_data, expected_status, headers={"content-type": "application/json"})
        mock_query.return_value = res
        data, status_code = await client._query_json(
            api_version="/v232435",
            path="/example",
            query=None,
            method="GET",
            data=None,
            headers=None,
            timeout=None,
            read_until_eof=True,
        )
        assert identical(data, expected_data)
        assert status_code == expected_status


@pytest.mark.asyncio
async def test_query(client, data_recordsets_function):
    expected_data = data_recordsets_function["data_single_recordset"]
    expected_status = HTTPStatus.OK
    with mock.patch("feihua.client.Client._do_query") as mock_do_query:
        res = MockResponse(expected_data, expected_status, headers={"content-type": "application/json"})
        mock_do_query.return_value = res
        async_cm = client._query(
            api_version="/v232435",
            path="/example",
        )
        async with async_cm:
            assert isinstance(async_cm, _AsyncCM)
            assert "__aenter__" in dir(async_cm)
            assert "__aexit__" in dir(async_cm)


@pytest.mark.parametrize(
    "name_data, expected_status, error, catch_error",
    [
        ("data_single_recordset", HTTPStatus.ACCEPTED, False, False),
        ("data_single_recordset", HTTPStatus.ACCEPTED, TimeoutError, TimeoutError),
        ("data_single_recordset", HTTPStatus.ACCEPTED, ClientConnectionError, ClientError),
        ("data_single_recordset", HTTPStatus.BAD_REQUEST, ClientConnectionError, ClientError),
    ],
)
@pytest.mark.asyncio
async def test_do_query(client, data_recordsets_function, name_data, expected_status, error, catch_error):
    expected_data = data_recordsets_function["data_single_recordset"]
    res = MockResponse(expected_data, expected_status, headers={"content-type": "application/json"})
    if not error:
        with mock.patch("aiohttp.ClientSession.request", make_mocked_coro(res)):

            data = await client._do_query(
                api_version="/v232435",
                path="/example",
            )
            assert data.status == expected_status
            assert await data.json() == expected_data
    else:
        with mock.patch("aiohttp.ClientSession.request", side_effect=error):
            with pytest.raises(catch_error):
                await client._do_query(
                    api_version="/v232435",
                    path="/example",
                )


@pytest.mark.parametrize(
    "name_data, expected_status, content_type",
    [
        ("data_error_text", HTTPStatus.BAD_REQUEST, "application/json"),
        ("data_error_text", HTTPStatus.INTERNAL_SERVER_ERROR, "application/json"),
        ("data_error_text", HTTPStatus.BAD_REQUEST, "text/plain"),
    ],
)
@pytest.mark.asyncio
async def test_do_query_catch_exaptions(client, data_recordsets_function, name_data, expected_status, content_type):
    expected_data = data_recordsets_function[name_data]
    res = MockResponse(expected_data, expected_status, headers={"content-type": content_type})
    with mock.patch("aiohttp.ClientSession.request", make_mocked_coro(res)):
        with pytest.raises(ClientError) as excinfo:
            await client._do_query(api_version="/v232435", path="/example")
        assert excinfo.value.status == expected_status
        if content_type == "text/plain":

            assert excinfo.value.message == json.dumps(expected_data)
        else:
            assert excinfo.value.message == expected_data["message"]
