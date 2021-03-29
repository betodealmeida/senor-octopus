from datetime import datetime
from datetime import timezone
from unittest import mock

import pytest
from freezegun import freeze_time
from senor_octopus.sources.speed import speed

mock_payload = {
    "download": 20932433.00558606,
    "upload": 6068322.252775613,
    "ping": 50.377,
    "server": {
        "url": "http://speedtest1.st-tel.net:8080/speedtest/upload.php",
        "lat": "39.3958",
        "lon": "-101.0519",
        "name": "Colby, KS",
        "country": "United States",
        "cc": "US",
        "sponsor": "S&T Communications",
        "id": "3434",
        "host": "speedtest1.st-tel.net:8080",
        "d": 1896.6996055651487,
        "latency": 50.377,
    },
    "timestamp": "2021-03-24T00:56:23.048266Z",
    "bytes_sent": 8364032,
    "bytes_received": 26295792,
    "share": None,
    "client": {
        "ip": "66.220.13.38",
        "lat": "38.3479",
        "lon": "-122.9737",
        "isp": "Hurricane Electric",
        "isprating": "3.7",
        "rating": "0",
        "ispdlavg": "0",
        "ispulavg": "0",
        "loggedin": "0",
        "country": "US",
    },
}


@freeze_time("2021-01-01")
@pytest.mark.asyncio
async def test_speed(mocker) -> None:
    mock_speedtest = mock.MagicMock()
    mock_speedtest.Speedtest.return_value.results.dict.return_value = mock_payload
    mocker.patch("senor_octopus.sources.speed.speedtest", mock_speedtest)

    events = [event async for event in speed()]
    print(events)
    assert events == [
        {
            "timestamp": datetime(2021, 1, 1, 0, 0, tzinfo=timezone.utc),
            "name": "hub.speedtest.download",
            "value": 20932433.00558606,
        },
        {
            "timestamp": datetime(2021, 1, 1, 0, 0, tzinfo=timezone.utc),
            "name": "hub.speedtest.upload",
            "value": 6068322.252775613,
        },
        {
            "timestamp": datetime(2021, 1, 1, 0, 0, tzinfo=timezone.utc),
            "name": "hub.speedtest.ping",
            "value": 50.377,
        },
        {
            "timestamp": datetime(2021, 1, 1, 0, 0, tzinfo=timezone.utc),
            "name": "hub.speedtest.server",
            "value": {
                "url": "http://speedtest1.st-tel.net:8080/speedtest/upload.php",
                "lat": "39.3958",
                "lon": "-101.0519",
                "name": "Colby, KS",
                "country": "United States",
                "cc": "US",
                "sponsor": "S&T Communications",
                "id": "3434",
                "host": "speedtest1.st-tel.net:8080",
                "d": 1896.6996055651487,
                "latency": 50.377,
            },
        },
        {
            "timestamp": datetime(2021, 1, 1, 0, 0, tzinfo=timezone.utc),
            "name": "hub.speedtest.timestamp",
            "value": "2021-03-24T00:56:23.048266Z",
        },
        {
            "timestamp": datetime(2021, 1, 1, 0, 0, tzinfo=timezone.utc),
            "name": "hub.speedtest.bytes_sent",
            "value": 8364032,
        },
        {
            "timestamp": datetime(2021, 1, 1, 0, 0, tzinfo=timezone.utc),
            "name": "hub.speedtest.bytes_received",
            "value": 26295792,
        },
        {
            "timestamp": datetime(2021, 1, 1, 0, 0, tzinfo=timezone.utc),
            "name": "hub.speedtest.share",
            "value": None,
        },
        {
            "timestamp": datetime(2021, 1, 1, 0, 0, tzinfo=timezone.utc),
            "name": "hub.speedtest.client",
            "value": {
                "ip": "66.220.13.38",
                "lat": "38.3479",
                "lon": "-122.9737",
                "isp": "Hurricane Electric",
                "isprating": "3.7",
                "rating": "0",
                "ispdlavg": "0",
                "ispulavg": "0",
                "loggedin": "0",
                "country": "US",
            },
        },
    ]
