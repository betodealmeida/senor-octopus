import logging
import os

import psycopg2
from psycopg2 import sql
from senor_octopus.types import Stream

_logger = logging.getLogger(__name__)


def postgresql(stream: Stream, table: str = "events") -> None:
    dbname = os.environ["POSTGRES_DBNAME"]
    user = os.environ["POSTGRES_USER"]
    password = os.environ["POSTGRES_PASSWORD"]
    with psycopg2.connect(dbname=dbname, user=user, password=password) as connection:
        with connection.cursor() as cursor:
            _logger.info("Trying to create table `%s`...", table)
            cursor.execute(
                sql.SQL(
                    """
                        CREATE TABLE IF NOT EXISTS {} (
                            "timestamp" TIMESTAMP,
                            "name" VARCHAR,
                            "value" NUMERIC
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
                    (event["timestamp"], event["name"], event["value"]),
                )
