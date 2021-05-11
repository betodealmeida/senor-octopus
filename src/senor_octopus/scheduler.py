import asyncio
import logging
from typing import Awaitable
from typing import Dict
from typing import List
from typing import Set

from senor_octopus.graph import Source

_logger = logging.getLogger(__name__)


async def log_exceptions(run: Awaitable[None]) -> None:
    """
    Manually handle exceptions.

    https://bugs.python.org/issue39839
    """
    try:
        return await run
    except Exception:
        _logger.exception("Unhandled exception")
    return None


class Scheduler:
    def __init__(self, dag: Set[Source]):
        self.dag = dag
        self.tasks: List[asyncio.Task] = []
        self.cancelled = False

    async def run(self) -> None:
        if not self.dag:
            _logger.info("Nothing to run")
            return

        _logger.info("Starting scheduler")
        loop = asyncio.get_event_loop()

        event_nodes = {node for node in self.dag if not node.schedule}
        for node in event_nodes:
            _logger.debug("Starting %s", node.name)
            task = asyncio.create_task(log_exceptions(node.run()))
            self.tasks.append(task)

        schedule_nodes = {node for node in self.dag if node.schedule}
        schedules: Dict[str, float] = {}
        while not self.cancelled:
            for node in schedule_nodes:
                now = loop.time()
                delay = node.schedule.next(default_utc=False)
                when = now + delay

                if node.name in schedules and schedules[node.name] <= now:
                    _logger.info("Running %s", node.name)
                    task = asyncio.create_task(log_exceptions(node.run()))
                    self.tasks.append(task)
                    del schedules[node.name]

                if node.name not in schedules:
                    _logger.info("Scheduling %s to run in %d seconds", node.name, delay)
                    schedules[node.name] = when

            self.tasks = [task for task in self.tasks if not task.done()]

            sleep_time = min(schedules.values()) - now if schedules else 3600
            _logger.debug("Sleeping for %d seconds", sleep_time)
            await asyncio.sleep(sleep_time)

    def cancel(self) -> None:
        for task in self.tasks:
            task.cancel()
        self.cancelled = True
