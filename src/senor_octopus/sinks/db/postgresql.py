import logging
import textwrap

import aiopg
from psycopg2 import sql
from psycopg2.extras import Json
from senor_octopus.types import Stream

_logger = logging.getLogger(__name__)


async def postgresql(
    stream: Stream,
    user: str,
    password: str,
    host: str,
    port: int,
    dbname: str,
    table: str = "events",
) -> None:
    """
    Write events into a Postgres database.

    This sink can be used to write events into a Postgres database.
    It will create a table with 3 columns, `timestamp`, `name` and
    `event`, where to events will be stored.

    Parameters
    ----------
    stream
        The incoming stream of events
    user
        The username to use when connecting to the DB
    password
        The password to use when connecting to the DB
    host
        Host where the database is running
    post
        Port which the database is listening to
    dbname
        Name of the database to connect to
    table
        Name of the table where the events will be stored
    """
    dsn = f"dbname={dbname} user={user} password={password} host={host} port={port}"
    async with aiopg.create_pool(dsn) as pool:
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                _logger.debug("Trying to create table `%s`", table)
                await cur.execute(
                    sql.SQL(
                        textwrap.dedent(
                            """
                            CREATE TABLE IF NOT EXISTS {table} (
                                "timestamp" TIMESTAMP,
                                "name" VARCHAR,
                                "value" JSON
                            );
                            """,
                        ),
                    ).format(table=sql.Identifier(table)),
                )
                _logger.debug("Trying to create index `%s_name_idx`", table)
                await cur.execute(
                    sql.SQL(
                        textwrap.dedent(
                            """
                            CREATE INDEX IF NOT EXISTS {index}
                            ON {table} USING HASH(name);
                            """,
                        ),
                    ).format(
                        table=sql.Identifier(table),
                        index=sql.Identifier(f"{table}_name_idx"),
                    ),
                )

                _logger.info("Inserting events into Postgres")
                async for event in stream:  # pragma: no cover
                    _logger.debug(event)
                    await cur.execute(
                        sql.SQL(
                            textwrap.dedent(
                                """
                                INSERT INTO {table} ("timestamp", "name", "value")
                                VALUES (%s, %s, %s);
                                """,
                            ),
                        ).format(table=sql.Identifier(table)),
                        (event["timestamp"], event["name"], Json(event["value"])),
                    )
