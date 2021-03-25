from unittest import mock

import aiotools
import pytest
from asynctest import CoroutineMock
from senor_octopus.scheduler import Scheduler


@pytest.mark.asyncio
async def test_scheduler() -> None:
    mock_source1 = mock.MagicMock()
    mock_source1.schedule.next.return_value = 10
    mock_source1.run = CoroutineMock()
    mock_source1.run.side_effect = [None, None, Exception("Stopped")]
    mock_source2 = mock.MagicMock()
    mock_source2.schedule = None
    mock_dag = {mock_source1, mock_source2}
    vclock = aiotools.VirtualClock()

    with vclock.patch_loop():
        scheduler = Scheduler(mock_dag)  # type: ignore
        with pytest.raises(Exception) as excinfo:
            await scheduler.run()

    assert str(excinfo.value) == "Stopped"
    assert len(mock_source1.run.mock_calls) == 3


@pytest.mark.asyncio
async def test_scheduler_no_jobs() -> None:
    vclock = aiotools.VirtualClock()
    with vclock.patch_loop():
        scheduler = Scheduler({})  # type: ignore
        await scheduler.run()
