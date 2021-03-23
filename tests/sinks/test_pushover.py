import os
import random

import pytest
from senor_octopus.sinks.pushover import pushover
from senor_octopus.sources.rand import rand


@pytest.mark.asyncio
async def test_pushover(mocker, httpx_mock) -> None:
    mocker.patch.dict(
        os.environ,
        {
            "PUSHOVER_APP_TOKEN": "XXX",
            "PUSHOVER_USER_TOKEN": "alice",
        },
    )
    httpx_mock.add_response()
    random.seed(42)

    await pushover(rand(2))
    requests = httpx_mock.get_requests()
    assert len(requests) == 2
    assert (
        requests[0].read()
        == b"token=XXX&user=alice&message=hub.random%3A+0.6394267984578837"
    )


@pytest.mark.asyncio
async def test_pushover_empty_stream(mocker, httpx_mock) -> None:
    mocker.patch.dict(
        os.environ,
        {
            "PUSHOVER_APP_TOKEN": "XXX",
            "PUSHOVER_USER_TOKEN": "alice",
        },
    )
    random.seed(42)

    await pushover(rand(0))
    assert not httpx_mock.get_request()
