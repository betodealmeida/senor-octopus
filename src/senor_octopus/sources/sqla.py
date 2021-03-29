import logging
from datetime import datetime
from datetime import timezone

from senor_octopus.types import Stream
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

_logger = logging.getLogger(__name__)


async def sqla(uri: str, sql: str) -> Stream:
    _logger.info("Running SQL query")
    _logger.debug(sql)

    engine = create_async_engine(uri)
    async with engine.connect() as conn:
        for row in await conn.execute(text(sql)):
            _logger.debug(row)
            event = dict(row)
            yield {
                "timestamp": event.get("timestamp", datetime.now(timezone.utc)),
                "name": event["name"],
                "value": event["value"],
            }
