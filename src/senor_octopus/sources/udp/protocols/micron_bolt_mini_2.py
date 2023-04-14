"""
An UDP protocol for the Micron Bolt Mini 2 GPS tracker.
"""

import asyncio
import logging
from typing import List, Optional, Tuple, cast

import requests

_logger = logging.getLogger(__name__)


class MicronBoltMini2UDPProtocol(asyncio.DatagramProtocol):
    """
    An UDP protocol for the Micron Bolt Mini 2 GPS tracker.
    """

    def __init__(self, queue: asyncio.Queue, api_key: Optional[str] = None) -> None:
        self.queue = queue
        self.api_key = api_key
        self.transport: Optional[asyncio.DatagramTransport] = None

    def connection_made(self, transport: asyncio.BaseTransport) -> None:
        self.transport = cast(asyncio.DatagramTransport, transport)

    def datagram_received(self, data: bytes, addr: Tuple[str, int]) -> None:
        if self.transport is None:
            return

        _logger.debug("Received %r from %s", data, addr)

        message = data.decode()
        parts = message.split(",")
        count = parts[-1].rstrip("$")
        reply = f"+SACK:{count}$\r\n"

        # heartbeat
        if parts[0] == "+ACK:GTHBD":
            protocol = parts[1]
            reply = f"+SACK:GTHBD,{protocol},{count}$\r\n"

        # WIFI information
        elif self.api_key and parts[0] in {"+RESP:GTWIF", "+BUFF:GTWIF"}:
            wifi_tokens = parts[5:-7]
            wifi_access_points: List[Tuple[str, int]] = []
            while wifi_tokens:
                mac_address, signal_strength = wifi_tokens[:2]
                wifi_tokens = wifi_tokens[5:]
                wifi_access_points.append((mac_address, int(signal_strength)))

            payload = {
                "considerIp": False,
                "wifiAccessPoints": wifi_access_points,
            }
            response = requests.post(
                "https://www.googleapis.com/geolocation/v1/geolocate",
                params={"key": self.api_key},
                json=payload,
            )
            if response.ok:
                result = response.json()
                value = {
                    "latitude": result["location"]["lat"],
                    "longitude": result["location"]["lng"],
                    "accuracy": result["accuracy"],
                }
                self.queue.put_nowait(value)

        # GPS information
        elif parts[0] in {"+RESP:GTFRI", "+BUFF:GTFRI"}:
            value = {
                "latitude": float(parts[12]),
                "longitude": float(parts[11]),
                "accuracy": float(parts[7]),
            }
            self.queue.put_nowait(value)

        self.transport.sendto(reply.encode(), addr)
