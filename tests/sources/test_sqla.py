from datetime import datetime
from datetime import timezone

import pytest
from freezegun import freeze_time
from senor_octopus.sources.sqla import sqla


results = [
    {
        "timestamp": datetime(2020, 12, 31, 0, 0, tzinfo=timezone.utc),
        "name": "foo",
        "value": "bar",
    },
    {"name": "foo", "value": "baz"},
]


@freeze_time("2021-01-01")
@pytest.mark.asyncio
async def test_sqla(mocker) -> None:
    mock = mocker.patch("senor_octopus.sources.sqla.create_async_engine")
    mock_conn = (
        mock.return_value.connect.return_value.__aenter__.return_value
    ) = mocker.MagicMock()
    mock_conn.execute = mocker.AsyncMock()
    mock_conn.execute.return_value = results

    events = [event async for event in sqla("uri", "sql")]
    assert events == [
        {
            "timestamp": datetime(2020, 12, 31, 0, 0, tzinfo=timezone.utc),
            "name": "hub.sqla.foo",
            "value": "bar",
        },
        {
            "timestamp": datetime(2021, 1, 1, 0, 0, tzinfo=timezone.utc),
            "name": "hub.sqla.foo",
            "value": "baz",
        },
    ]
