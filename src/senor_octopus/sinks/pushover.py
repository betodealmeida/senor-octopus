import logging

import httpx
from senor_octopus.types import Stream

_logger = logging.getLogger(__name__)


async def pushover(stream: Stream, app_token: str, user_token: str) -> None:
    """
    Send events to the Pushover mobile app.

    This sink can be used to send events to a smartphone, using
    the Pushover (pushover.net) application.

    Parameters
    ----------
    stream
        The incoming stream of events
    app_token
        The application token (https://pushover.net/api)
    user_token
        The user token (https://pushover.net/api)
    """
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
