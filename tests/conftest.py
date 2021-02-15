import asyncio

import pytest

from feihua.client import Client


@pytest.fixture
def event_loop(request):
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def client(event_loop):
    access_key_id = "example"
    secret_access_key = "example"
    host = "dns.zone.ru"

    async def _make_client():
        return Client(access_key_id=access_key_id, secret_access_key=secret_access_key, host=host)

    client = event_loop.run_until_complete(_make_client())
    yield client

    async def _finalize():
        await client.close()

    event_loop.run_until_complete(_finalize())
