"""
Tests for ``sink.db.postgresql``.
"""

# pylint: disable=redefined-outer-name

import random
from datetime import datetime, timezone
from typing import AsyncGenerator
from unittest.mock import ANY, AsyncMock, call

import pytest
import pytest_asyncio
from freezegun import freeze_time
from psycopg2 import sql
from pytest_mock import MockerFixture

from senor_octopus.sinks.db.postgresql import postgresql
from senor_octopus.sources.rand import rand


class AsyncContextManager:
    """
    Mock an async context manager.
    """

    async def __aenter__(self):
        pass

    async def __aexit__(self, exc_type, exc, traceback):
        pass


@pytest_asyncio.fixture
async def cursor(mocker: MockerFixture) -> AsyncGenerator[AsyncMock, None]:
    """
    Mock a cursor.
    """
    aiopg = mocker.MagicMock()
    aiopg.create_pool = mocker.MagicMock(AsyncContextManager)
    pool = aiopg.create_pool().__aenter__.return_value
    pool.acquire = mocker.MagicMock(AsyncContextManager)
    conn = pool.acquire().__aenter__.return_value
    conn.cursor = mocker.MagicMock(AsyncContextManager)
    cursor = conn.cursor().__aenter__.return_value

    mocker.patch("senor_octopus.sinks.db.postgresql.aiopg", aiopg)
    yield cursor


@freeze_time("2021-01-01")
@pytest.mark.asyncio
async def test_postgresql(cursor: AsyncMock) -> None:
    """
    Tests for the sink.
    """
    random.seed(42)

    await postgresql(rand(1), "user", "password", "host", 5432, "dbname")

    cursor.execute.assert_has_calls(
        [
            call(
                sql.Composed(
                    [
                        sql.SQL("\nCREATE TABLE IF NOT EXISTS "),
                        sql.Identifier("events"),
                        sql.SQL(
                            ' (\n    "timestamp" TIMESTAMP,\n    '
                            '"name" VARCHAR,\n    "value" JSON\n);\n',
                        ),
                    ],
                ),
            ),
            call(
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
            call(
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
                    ANY,  # Json(0.6394267984578837)
                ),
            ),
        ],
    )


@pytest.mark.asyncio
async def test_postgresql_empty_stream(cursor: AsyncMock) -> None:
    """
    Test that the sink works with an empty stream.
    """
    random.seed(42)

    await postgresql(rand(0), "user", "password", "host", 5432, "dbname")

    assert cursor.execute.call_count == 2
