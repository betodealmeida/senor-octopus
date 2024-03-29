"""
A simple SMS sink.

This sink uses the Twilio API to send SMS messages.
"""

import logging

from twilio.rest import Client

from senor_octopus.types import Stream

_logger = logging.getLogger(__name__)


async def sms(
    stream: Stream,
    account_sid: str,
    auth_token: str,
    to: str,  # pylint: disable=invalid-name
    **kwargs: str,
) -> None:
    """
    Send SMS via Twilio.

    Parameters
    ----------
    stream
        The incoming stream of events
    account_sid
        The account SID (https://www.twilio.com/console)
    auth_token
        The auth token (https://www.twilio.com/console)
    from
        Twilio phone number
    to
        Recipient phone number
    """
    from_ = kwargs["from"]
    client = Client(account_sid, auth_token)

    async for event in stream:  # pragma: no cover
        _logger.debug(event)
        _logger.info("Sending SMS")
        client.messages.create(body=str(event["value"]).strip(), from_=from_, to=to)
