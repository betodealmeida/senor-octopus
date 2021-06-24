import logging

from senor_octopus.types import Stream
from slack_sdk import WebClient

_logger = logging.getLogger(__name__)


async def slack(
    stream: Stream,
    token: str,
    channel: str,
) -> None:
    """
    Send events as messages to a Slack channel.

    This sink can be used to send events to a Slack channel.
    The value of the event is sent as the message; its name
    is ignored.

    Parameters
    ----------
    stream
        The incoming stream of events
    token
        The authentication token for the bot
    channel
        The Slack channel ID
    """
    client = WebClient(token=token)
    async for event in stream:  # pragma: no cover
        client.chat_postMessage(channel=channel, text=str(event["value"]))
