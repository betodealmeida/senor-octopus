import logging
from datetime import datetime
from datetime import timezone
from typing import List
from typing import Union

import cryptocompare
from senor_octopus.types import Stream

_logger = logging.getLogger(__name__)


async def crypto(
    coins: Union[str, List[str]],
    currency: str = "USD",
    prefix: str = "hub.crypto",
) -> Stream:
    _logger.info("Fetching crypto data")

    if isinstance(coins, str):
        coins = [coin.strip() for coin in coins.split(",")]

    for coin in coins:
        info = cryptocompare.get_price(coin, currency=currency, full=False)
        value = info[coin][currency]
        _logger.debug("%s: %s %s", coin, currency, value)
        yield {
            "timestamp": datetime.now(timezone.utc),
            "name": f"{prefix}.{coin}.{currency}",
            "value": value,
        }
