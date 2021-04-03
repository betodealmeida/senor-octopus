import logging
from datetime import datetime
from datetime import timezone
from typing import List

import stockquotes
from senor_octopus.types import Stream

_logger = logging.getLogger(__name__)


async def stock(symbols: List[str], prefix: str = "hub.stock") -> Stream:
    _logger.info("Fetching stock data")

    for symbol in symbols:
        ticker = stockquotes.Stock(symbol)
        for attribute in {"current_price", "increase_percent"}:
            value = getattr(ticker, attribute)
            _logger.debug(
                "%s (%s) %s: %s",
                ticker.symbol,
                ticker.name,
                attribute,
                value,
            )
            yield {
                "timestamp": datetime.now(timezone.utc),
                "name": f"{prefix}.{symbol}.{attribute}",
                "value": value,
            }
