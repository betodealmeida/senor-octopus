import logging
import os

import psycopg2
from psycopg2 import sql
from psycopg2.extras import Json
from senor_octopus.types import Stream

_logger = logging.getLogger(__name__)


def postgresql(stream: Stream, table: str = "events") -> None:
    dbname = os.environ["POSTGRES_DBNAME"]
    host = os.environ["POSTGRES_HOST"]
    port = os.environ["POSTGRES_PORT"]
    user = os.environ["POSTGRES_USER"]
    password = os.environ["POSTGRES_PASSWORD"]
    with psycopg2.connect(
        dbname=dbname,
        host=host,
        port=port,
        user=user,
        password=password,
    ) as connection:
        with connection.cursor() as cursor:
            _logger.info("Trying to create table `%s`...", table)
            cursor.execute(
                sql.SQL(
                    """
                        CREATE TABLE IF NOT EXISTS {} (
                            "timestamp" TIMESTAMP,
                            "name" VARCHAR,
                            "value" JSON
                        );
                    """,
                ).format(sql.Identifier(table)),
            )
            for event in stream:
                _logger.info("Inserting event into Postgres...")
                cursor.execute(
                    sql.SQL(
                        """
                            INSERT INTO {} ("timestamp", "name", "value")
                            VALUES (%s, %s, %s);
                        """,
                    ).format(sql.Identifier(table)),
                    (event["timestamp"], event["name"], Json(event["value"])),
                )
