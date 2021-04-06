import random

import pytest
from senor_octopus.sinks.pushover import pushover
from senor_octopus.sources.rand import rand


@pytest.mark.asyncio
async def test_pushover(httpx_mock) -> None:
    httpx_mock.add_response()
    random.seed(42)

    await pushover(rand(2), "XXX", "alice")
    requests = httpx_mock.get_requests()
    assert len(requests) == 2
    assert (
        requests[0].read()
        == b"token=XXX&user=alice&message=hub.random%3A+0.6394267984578837"
    )


@pytest.mark.asyncio
async def test_pushover_empty_stream(httpx_mock) -> None:
    random.seed(42)

    await pushover(rand(0), "XXX", "alice")
    assert not httpx_mock.get_request()
