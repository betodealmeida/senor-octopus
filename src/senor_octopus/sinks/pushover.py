import logging
import os

import httpx
from senor_octopus.types import Stream

_logger = logging.getLogger(__name__)


async def pushover(stream: Stream) -> None:
    app_token = os.environ["PUSHOVER_APP_TOKEN"]
    user_token = os.environ["PUSHOVER_USER_TOKEN"]

    url = "https://api.pushover.net/1/messages.json"
    async for event in stream:  # pragma: no cover
        _logger.debug(event)
        data = {
            "token": app_token,
            "user": user_token,
            "message": "{name}: {value}".format(**event),
        }
        _logger.info("Posting message to Pushover")
        async with httpx.AsyncClient() as client:
            await client.post(url, data=data)
