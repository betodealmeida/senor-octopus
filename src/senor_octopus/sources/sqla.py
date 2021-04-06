import logging
from datetime import datetime
from datetime import timezone

from senor_octopus.types import Stream
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

_logger = logging.getLogger(__name__)


async def sqla(uri: str, sql: str, prefix: str = "hub.sqla") -> Stream:
    """
    Read data from database.

    The SQLAlchemy source periodically reads data from a database. It
    uses a query that MUST return at least two columns: `name` and `value`.
    Optionally, it an also return a column called `timestamp`, which will
    be used as the timestamp of the generated event. Otherwise, the current
    timestamp will be used.

    Parameters
    ----------
    uri
        SQLAlchemy URI (https://docs.sqlalchemy.org/en/14/core/engines.html)
    sql
        SQL query to run
    prefix
        Prefix for events from this source

    Yields
    ------
    Event
        Events with rows from database
    """
    _logger.info("Running SQL query")
    _logger.debug(sql)

    engine = create_async_engine(uri)
    async with engine.connect() as conn:
        for row in await conn.execute(text(sql)):
            _logger.debug(row)
            event = dict(row)
            yield {
                "timestamp": event.get("timestamp", datetime.now(timezone.utc)),
                "name": f"{prefix}.{event['name']}",
                "value": event["value"],
            }
