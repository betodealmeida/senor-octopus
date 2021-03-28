import asyncio
import logging
from typing import Dict
from typing import List
from typing import Set

from senor_octopus.graph import Source

_logger = logging.getLogger(__name__)


SLEEP_TIME = 5


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
            task = asyncio.create_task(node.run())
            self.tasks.append(task)

        schedule_nodes = {node for node in self.dag if node.schedule}
        schedules: Dict[str, float] = {}
        while not self.cancelled:
            for node in schedule_nodes:
                now = loop.time()
                delay = node.schedule.next(default_utc=False)
                when = now + delay

                if node.name not in schedules:
                    _logger.info(f"Scheduling {node.name} to run in {delay} seconds")
                    schedules[node.name] = when
                elif schedules[node.name] <= now:
                    _logger.info(f"Running {node.name}")
                    task = asyncio.create_task(node.run())
                    self.tasks.append(task)
                    del schedules[node.name]

            _logger.debug(f"Sleeping for {SLEEP_TIME} seconds")
            await asyncio.sleep(SLEEP_TIME)

    def cancel(self) -> None:
        for task in self.tasks:
            task.cancel()
        self.cancelled = True
