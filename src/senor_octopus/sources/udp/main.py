"""
UDP source.
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any

from pkg_resources import iter_entry_points

from senor_octopus.types import Stream

_logger = logging.getLogger(__name__)


async def udp(
    protocol: str,
    host: str = "localhost",
    port: int = 5000,
    prefix: str = "hub.udp",
    **kwargs: Any,
) -> Stream:
    """
    Listen to UDP datagrams in a given port.

    Parameters
    ----------
    protocol
        Protocol to use for decoding the datagrams
    host
        Hostname or IP address to listen to
    port
        Port to listen to
    prefix
        Prefix to use for the stream
    kwargs
        Additional keyword arguments to pass to the protocol

    Yields
    ------
    Event
        Events with messages processed by the protocol
    """
    queue: asyncio.Queue = asyncio.Queue()

    try:
        protocol_class = next(
            iter_entry_points("senor_octopus.source.udp.protocols", protocol),
        ).load()
    except StopIteration as ex:
        raise Exception(f'Protocol "{protocol}" not found') from ex

    while True:
        loop = asyncio.get_running_loop()
        transport, _ = await loop.create_datagram_endpoint(  # pragma: no cover
            lambda: protocol_class(queue, **kwargs),
            local_addr=(host, port),
        )
        try:
            while True:
                value = await queue.get()
                yield {
                    "timestamp": datetime.now(timezone.utc),
                    "name": f"{prefix}.message",
                    "value": value,
                }
        except asyncio.CancelledError:
            break
        finally:
            transport.close()
