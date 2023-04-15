"""
Tests for the UDP source.
"""

import asyncio
from datetime import datetime, timezone

import aiotools
import pytest
from freezegun import freeze_time
from pytest_mock import MockerFixture

from senor_octopus.sources.udp.main import udp


@freeze_time("2022-01-01T12:00:00-07:00")
@pytest.mark.asyncio
async def test_udp(mocker: MockerFixture) -> None:
    """
    Tests for the ``udp`` source.
    """
    mocker.patch("senor_octopus.sources.udp.main.iter_entry_points")

    mock_asyncio = mocker.patch("senor_octopus.sources.udp.main.asyncio")
    mock_asyncio.CancelledError = asyncio.CancelledError
    mock_asyncio.Queue().get = mocker.AsyncMock(
        side_effect=[
            {"foo": "bar"},
            asyncio.CancelledError("Canceled"),
        ]
    )
    loop = mock_asyncio.get_running_loop.return_value = mocker.AsyncMock()
    transport = mocker.MagicMock()
    protocol = mocker.MagicMock()
    loop.create_datagram_endpoint.return_value = transport, protocol

    vclock = aiotools.VirtualClock()
    with vclock.patch_loop():
        events = [event async for event in udp("DummyProtocol")]

    assert events == [
        {
            "name": "hub.udp.message",
            "timestamp": datetime(2022, 1, 1, 19, 0, tzinfo=timezone.utc),
            "value": {"foo": "bar"},
        }
    ]


@pytest.mark.asyncio
async def test_udp_invalid_protocol(mocker: MockerFixture) -> None:
    """
    Test the ``udp`` source when the protocol is invalid.
    """
    mocker.patch(
        "senor_octopus.sources.udp.main.iter_entry_points",
        return_value=iter([]),
    )

    mocker.patch("senor_octopus.sources.udp.main.asyncio")

    with pytest.raises(Exception, match='Protocol "DummyProtocol" not found'):
        [event async for event in udp("DummyProtocol")]
