import logging
import os

import requests
from senor_octopus.types import Stream

_logger = logging.getLogger(__name__)


def pushover(stream: Stream) -> None:
    app_token = os.environ["PUSHOVER_APP_TOKEN"]
    user_token = os.environ["PUSHOVER_USER_TOKEN"]
    url = "https://api.pushover.net/1/messages.json"
    for event in stream:
        _logger.info("Posting message to Pushover...")
        data = {
            "token": app_token,
            "user": user_token,
            "message": "{name}: {value}".format(**event),
        }
        requests.post(url, data=data)
