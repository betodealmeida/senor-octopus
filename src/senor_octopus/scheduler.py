import asyncio
import logging
from collections import defaultdict
from typing import Dict
from typing import Set

from senor_octopus.graph import Source

_logger = logging.getLogger(__name__)


class Scheduler:
    def __init__(self, dag: Set[Source], tolerance: int = 5):
        self.dag = dag
        self.tolerance = tolerance

    async def run(self) -> None:
        _logger.info("Starting scheduler...")

        while True:
            delays: Dict[int, Set[Source]] = defaultdict(set)
            for node in self.dag:
                if node.schedule:
                    next_run = int(node.schedule.next(default_utc=True))
                    next_run = next_run - next_run % self.tolerance
                    delays[next_run].add(node)
            min_delay = min(delays)
            _logger.info(f"Sleeping for {min_delay} seconds...")
            await asyncio.sleep(min_delay)
            await asyncio.gather(
                *[node.run() for node in delays[min_delay]], return_exceptions=True
            )
