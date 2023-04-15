"""
Tests for ``sink.pushover``.
"""

import random

import pytest

from senor_octopus.sinks.pushover import pushover
from senor_octopus.sources.rand import rand


@pytest.mark.asyncio
async def test_pushover(httpx_mock) -> None:
    """
    Test the source.
    """
    httpx_mock.add_response()
    random.seed(42)

    await pushover(rand(2), "XXX", "alice")
    requests = httpx_mock.get_requests()
    assert len(requests) == 2
    assert requests[0].read() == (
        b"token=XXX&user=alice&message=%7Bevent%5B%27name%27%5D%7D%3A+"
        b"%7Bevent%5B%27value%27%5D%7D"
    )


@pytest.mark.asyncio
async def test_pushover_empty_stream(httpx_mock) -> None:
    """
    Test that nothing is sent when the stream is empty.
    """
    random.seed(42)

    await pushover(rand(0), "XXX", "alice")
    assert not httpx_mock.get_request()
