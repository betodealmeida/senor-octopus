from unittest import mock

import pytest
from asynctest import CoroutineMock

from senor_octopus.scheduler import Scheduler


@pytest.mark.asyncio
async def test_scheduler() -> None:
    mock_source1 = mock.MagicMock()
    mock_source1.schedule.next.return_value = 0
    mock_source1.run = CoroutineMock()
    mock_source1.run.side_effect = [None, Exception("Stopped")]
    mock_source2 = mock.MagicMock()
    mock_source2.schedule = None
    mock_dag = {mock_source1, mock_source2}

    scheduler = Scheduler(mock_dag)
    with pytest.raises(Exception) as excinfo:
        await scheduler.run()

    assert str(excinfo.value) == "Stopped"
    assert len(mock_source1.run.mock_calls) == 2
