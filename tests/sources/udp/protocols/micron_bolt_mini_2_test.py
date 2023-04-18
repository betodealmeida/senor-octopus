"""
Tests for the Micron Bolt Mini 2 UDP GPS tracker protocol.
"""

import asyncio
from datetime import datetime, timezone

import pytest
from pytest_mock import MockerFixture
from requests_mock.mocker import Mocker

from senor_octopus.sources.udp.protocols.micron_bolt_mini_2 import (
    MicronBoltMini2UDPProtocol,
)


@pytest.mark.asyncio
async def test_micron_bolt_mini_2_no_connection(mocker: MockerFixture):
    """
    Test protocol when ``data_received`` is called before ``connection_made``.
    """
    _logger = mocker.patch(
        "senor_octopus.sources.udp.protocols.micron_bolt_mini_2._logger",
    )
    queue: asyncio.Queue = asyncio.Queue()
    protocol = MicronBoltMini2UDPProtocol(queue)
    addr = ("localhost", 5000)

    # no connection
    protocol.datagram_received(b"+SACK:GTHBD,423136,010C$\r\n", addr)
    _logger.assert_not_called()


@pytest.mark.asyncio
async def test_micron_bolt_mini_2_hearbeat(mocker: MockerFixture):
    """
    Test protocol heartbeat.
    """
    queue: asyncio.Queue = asyncio.Queue()
    protocol = MicronBoltMini2UDPProtocol(queue)
    transport = mocker.MagicMock()
    addr = ("localhost", 5000)

    protocol.connection_made(transport)
    protocol.datagram_received(
        b"+ACK:GTHBD,423136,352009117419957,,20230413184216,010C$",
        addr,
    )
    transport.sendto.assert_called_with(b"+SACK:GTHBD,423136,010C$\r\n", addr)


@pytest.mark.asyncio
async def test_micron_bolt_mini_2_gps(mocker: MockerFixture):
    """
    Test protocol handling a GPS report.
    """
    queue: asyncio.Queue = asyncio.Queue()
    protocol = MicronBoltMini2UDPProtocol(queue)
    transport = mocker.MagicMock()
    addr = ("localhost", 5000)

    protocol.connection_made(transport)
    protocol.datagram_received(
        (
            b"+RESP:GTFRI,423136,352009117419957,,0,0,1,1.0,0.0,62,"
            b"28.3,-122.990623,38.313342,20230414193420,310,260,38F2,"
            b"2D01A05,00,77,20230414193424,0297$"
        ),
        addr,
    )
    value = await queue.get()
    assert value == {
        "accuracy": 1.0,
        "altitude": 28.3,
        "azimuth": 62.0,
        "battery": 77.0,
        "fix_time": datetime(2023, 4, 14, 19, 34, 20, tzinfo=timezone.utc),
        "id": "352009117419957",
        "latitude": 38.313342,
        "longitude": -122.990623,
        "send_time": datetime(2023, 4, 14, 19, 34, 24, tzinfo=timezone.utc),
        "source": "gps",
        "speed": 0.0,
    }


@pytest.mark.asyncio
async def test_micron_bolt_mini_2_wifi_no_api_key(mocker: MockerFixture):
    """
    Test protocol on a Wifi report without an API key.
    """
    queue: asyncio.Queue = asyncio.Queue()
    protocol = MicronBoltMini2UDPProtocol(queue)
    transport = mocker.MagicMock()
    addr = ("localhost", 5000)

    protocol.connection_made(transport)
    protocol.datagram_received(
        (
            b"+RESP:GTWIF,423136,352009117419957,,4,b0e4d556fbc6,-58"
            b",,,,a4d79504102d,-73,,,,322f23291e0b,-78,,,,"
            b"44a56edcdae8,-88,,,,,,,,77,20230414193408,0295$"
        ),
        addr,
    )
    assert queue.empty()


@pytest.mark.asyncio
async def test_micron_bolt_mini_2_wifi(
    mocker: MockerFixture,
    requests_mock: Mocker,
):
    """
    Test protocol on a Wifi report.
    """
    requests_mock.post(
        "https://www.googleapis.com/geolocation/v1/geolocate?key=SECRET",
        json={"location": {"lat": 38.3130657, "lng": -122.9903798}, "accuracy": 20},
    )

    queue: asyncio.Queue = asyncio.Queue()
    protocol = MicronBoltMini2UDPProtocol(queue, "SECRET")
    transport = mocker.MagicMock()
    addr = ("localhost", 5000)

    protocol.connection_made(transport)
    protocol.datagram_received(
        (
            b"+RESP:GTWIF,423136,352009117419957,,4,b0e4d556fbc6,-58"
            b",,,,a4d79504102d,-73,,,,322f23291e0b,-78,,,,"
            b"44a56edcdae8,-88,,,,,,,,77,20230414193408,0295$"
        ),
        addr,
    )
    value = await queue.get()
    assert value == {
        "accuracy": 20,
        "battery": 77.0,
        "id": "352009117419957",
        "latitude": 38.3130657,
        "longitude": -122.9903798,
        "source": "wifi",
        "send_time": datetime(2023, 4, 14, 19, 34, 8, tzinfo=timezone.utc),
    }


@pytest.mark.asyncio
async def test_micron_bolt_mini_2_wifi_not_found(
    mocker: MockerFixture,
    requests_mock: Mocker,
):
    """
    Test protocol on a Wifi report when the geolocation fails.
    """
    requests_mock.post(
        "https://www.googleapis.com/geolocation/v1/geolocate?key=SECRET",
        json={
            "error": {
                "code": 404,
                "message": "Not Found",
                "errors": [
                    {
                        "message": "Not Found",
                        "domain": "geolocation",
                        "reason": "notFound",
                    },
                ],
            },
        },
        status_code=404,
    )

    queue: asyncio.Queue = asyncio.Queue()
    protocol = MicronBoltMini2UDPProtocol(queue, "SECRET")
    transport = mocker.MagicMock()
    addr = ("localhost", 5000)

    protocol.connection_made(transport)
    protocol.datagram_received(
        (
            b"+RESP:GTWIF,423136,352009117419957,,4,b0e4d556fbc6,-58"
            b",,,,a4d79504102d,-73,,,,322f23291e0b,-78,,,,"
            b"44a56edcdae8,-88,,,,,,,,77,20230414193408,0295$"
        ),
        addr,
    )
    assert queue.empty()
