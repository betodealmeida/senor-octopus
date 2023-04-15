"""
An UDP protocol for the Micron Bolt Mini 2 GPS tracker.
"""

import asyncio
import logging
import re
from typing import List, Optional, Tuple, TypedDict, cast

import requests

_logger = logging.getLogger(__name__)


class WifiAccessPointType(TypedDict):
    """
    A WiFi access point.
    """

    macAddress: str
    signalStrength: int


class MicronBoltMini2UDPProtocol(asyncio.DatagramProtocol):
    """
    An UDP protocol for the Micron Bolt Mini 2 GPS tracker.

    To configure it, send the following commands to the tracker via SMS:

        - AT+GTQSS=AIR11,${apn},,,4,,1,${host1},${port1},${host2},${port2},,10,1,,,0001$
        - AT+GTNMD=AIR11,8,2,4,15,240,,,,0002$
        - AT+GTFRI=AIR11,1,1,,,0000,2359,86400,1,86400,1,001F,1000,1000,,,,,,,0003$

    This will the device send GPS data once per day.

    If an API key is provided, the protocol will use the Google Geolocation service to
    determine the location of the device based on the WiFi access points it can see.
    """

    def __init__(self, queue: asyncio.Queue, api_key: Optional[str] = None) -> None:
        self.queue = queue
        self.api_key = api_key
        self.transport: Optional[asyncio.DatagramTransport] = None

    def connection_made(self, transport: asyncio.BaseTransport) -> None:
        self.transport = cast(asyncio.DatagramTransport, transport)

    # pylint: disable=too-many-locals
    def datagram_received(self, data: bytes, addr: Tuple[str, int]) -> None:
        """
        Handle incoming data.
        """
        if self.transport is None:
            return

        _logger.debug("Received %r from %s", data, addr)

        message = data.decode().strip()
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
            wifi_access_points: List[WifiAccessPointType] = []
            while wifi_tokens:
                mac_address, signal_strength = wifi_tokens[:2]
                wifi_tokens = wifi_tokens[5:]
                wifi_access_points.append(
                    {
                        "macAddress": re.sub(r"(..)", r"\1:", mac_address),
                        "signalStrength": int(signal_strength),
                    },
                )

            payload = {
                "considerIp": False,
                "wifiAccessPoints": wifi_access_points,
            }
            response = requests.post(
                "https://www.googleapis.com/geolocation/v1/geolocate",
                params={"key": self.api_key},
                json=payload,
                timeout=60,
            )
            if response.ok:
                result = response.json()
                value = {
                    "latitude": result["location"]["lat"],
                    "longitude": result["location"]["lng"],
                    "accuracy": result["accuracy"],
                    "battery": float(parts[-3]),
                    "source": "wifi",
                }
                self.queue.put_nowait(value)

        # GPS information
        elif parts[0] in {"+RESP:GTFRI", "+BUFF:GTFRI"}:
            value = {
                "latitude": float(parts[12]),
                "longitude": float(parts[11]),
                "accuracy": float(parts[7]),
                "battery": float(parts[-3]),
                "source": "gps",
            }
            self.queue.put_nowait(value)

        self.transport.sendto(reply.encode(), addr)
