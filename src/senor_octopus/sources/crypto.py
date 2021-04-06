import logging
from datetime import datetime
from datetime import timezone
from typing import List

import cryptocompare
from senor_octopus.types import Stream

_logger = logging.getLogger(__name__)


async def crypto(
    coins: List[str],
    currency: str = "USD",
    prefix: str = "hub.crypto",
) -> Stream:
    """
    Fetch price of cryptocurrencies from cryptocompare.com.

    This source will periodically retrieve the price of
    cryptocurrencies from the cryptocompare.com website.

    Parameters
    ----------
    coins
        List of cryptocurrency symbols
    currency
        Currency used to display price
    prefix
        Prefix for events from this source

    Yields
    ------
    Event
        Events with price of cryptocurrencies
    """
    _logger.info("Fetching crypto data")

    for coin in coins:
        info = cryptocompare.get_price(coin, currency=currency, full=False)
        value = info[coin][currency]
        _logger.debug("%s: %s %s", coin, currency, value)
        yield {
            "timestamp": datetime.now(timezone.utc),
            "name": f"{prefix}.{coin}.{currency}",
            "value": value,
        }
