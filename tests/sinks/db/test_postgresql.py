import random
from datetime import datetime
from datetime import timezone
from unittest import mock

import pytest
from asynctest import CoroutineMock
from freezegun import freeze_time
from psycopg2 import sql
from senor_octopus.sinks.db.postgresql import postgresql
from senor_octopus.sources.rand import rand


@freeze_time("2021-01-01")
@pytest.mark.asyncio
async def test_postgresql(mocker) -> None:
    mock_aiopg = CoroutineMock()
    mock_cursor = (
        mock_aiopg.create_pool.return_value.__aenter__.return_value.acquire.return_value.__aenter__.return_value.cursor.return_value.__aenter__.return_value
    )
    mock_cursor.execute = CoroutineMock()
    mocker.patch("senor_octopus.sinks.db.postgresql.aiopg", mock_aiopg)
    random.seed(42)

    await postgresql(rand(1), "user", "password", "host", 5432, "dbname")

    mock_cursor.execute.assert_has_calls(
        [
            mock.call(
                sql.Composed(
                    [
                        sql.SQL("\nCREATE TABLE IF NOT EXISTS "),
                        sql.Identifier("events"),
                        sql.SQL(
                            ' (\n    "timestamp" TIMESTAMP,\n    "name" VARCHAR,\n    "value" JSON\n);\n',
                        ),
                    ],
                ),
            ),
            mock.call(
                sql.Composed(
                    [
                        sql.SQL("\nCREATE INDEX IF NOT EXISTS "),
                        sql.Identifier("events_name_idx"),
                        sql.SQL("\nON "),
                        sql.Identifier("events"),
                        sql.SQL(" USING HASH(name);\n"),
                    ],
                ),
            ),
            mock.call(
                sql.Composed(
                    [
                        sql.SQL("\nINSERT INTO "),
                        sql.Identifier("events"),
                        sql.SQL(
                            ' ("timestamp", "name", "value")\nVALUES (%s, %s, %s);\n',
                        ),
                    ],
                ),
                (
                    datetime(2021, 1, 1, 0, 0, tzinfo=timezone.utc),
                    "hub.random",
                    mock.ANY,  # Json(0.6394267984578837)
                ),
            ),
        ],
    )


@pytest.mark.asyncio
async def test_postgresql_empty_stream(mocker) -> None:
    mock_aiopg = CoroutineMock()
    mock_cursor = (
        mock_aiopg.create_pool.return_value.__aenter__.return_value.acquire.return_value.__aenter__.return_value.cursor.return_value.__aenter__.return_value
    )
    mock_cursor.execute = CoroutineMock()
    mocker.patch("senor_octopus.sinks.db.postgresql.aiopg", mock_aiopg)
    random.seed(42)

    await postgresql(rand(0), "user", "password", "host", 5432, "dbname")
    assert len(mock_cursor.execute.mock_calls) == 2
