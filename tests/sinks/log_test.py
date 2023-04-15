"""
Tests for ``sink.log``.
"""

import random
from datetime import datetime, timezone

import pytest
from freezegun import freeze_time

from senor_octopus.sinks.log import log
from senor_octopus.sources.rand import rand


@pytest.mark.asyncio
@freeze_time("2021-01-01")
async def test_log(mocker) -> None:
    """
    Tests for the sink.
    """
    logging = mocker.patch("senor_octopus.sinks.log.logging")
    _logger = logging.getLogger()
    random.seed(42)

    await log(rand(1), level="INFO")
    _logger.log.assert_called_with(
        logging.INFO,
        {
            "timestamp": datetime(2021, 1, 1, 0, 0, tzinfo=timezone.utc),
            "name": "hub.random",
            "value": 0.6394267984578837,
        },
    )

    await log(rand(1), level="ERROR")
    _logger.log.assert_called_with(
        logging.ERROR,
        {
            "timestamp": datetime(2021, 1, 1, 0, 0, tzinfo=timezone.utc),
            "name": "hub.random",
            "value": 0.025010755222666936,
        },
    )
