from datetime import datetime

import pytest
from senor_octopus.sinks.tuya import tuya
from senor_octopus.types import Stream


async def stream() -> Stream:
    for value in {"on", "off", "invalid"}:
        yield {
            "timestamp": datetime(2021, 1, 1),
            "name": "turn",
            "value": value,
        }
    yield {
        "timestamp": datetime(2021, 1, 1),
        "name": "foo",
        "value": "bar",
    }


@pytest.mark.asyncio
async def test_tuya(mocker) -> None:
    mock_api = mocker.patch("senor_octopus.sinks.tuya.api")
    mock_device = mocker.MagicMock()
    mock_device.name.return_value = "My switch"
    mock_api.get_all_devices.return_value = [mock_device]

    mock_logger = mocker.patch("senor_octopus.sinks.tuya._logger")

    await tuya(stream(), "My switch", "user@example.com", "XXX", "1", "smart_life")

    mock_device.turn_on.assert_called()
    mock_device.turn_off.assert_called()
    mock_logger.warning.assert_called_with("Unknown value: %s", "invalid")


@pytest.mark.asyncio
async def test_tuya_invalid_device(mocker) -> None:
    mock_api = mocker.patch("senor_octopus.sinks.tuya.api")
    mock_device = mocker.MagicMock()
    mock_device.name.return_value = "My switch"
    mock_api.get_all_devices.return_value = [mock_device]

    mock_logger = mocker.patch("senor_octopus.sinks.tuya._logger")

    await tuya(stream(), "My new switch", "user@example.com", "XXX", "1", "smart_life")

    mock_logger.error.assert_called_with(
        'Device "%s" not found. Available devices: %s',
        "My new switch",
        '"My switch"',
    )
