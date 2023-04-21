"""
A source that reads data from an Awair Element monitor.
"""

import logging
from datetime import datetime, timezone

import httpx
from marshmallow import Schema, fields

from senor_octopus.lib import configuration_schema
from senor_octopus.types import Stream

_logger = logging.getLogger(__name__)


class AwairConfig(Schema):  # pylint: disable=too-few-public-methods
    """
    A source that reads air quality data from an Awair Element monitor.
    """

    access_token = fields.String(
        required=True,
        default=None,
        title="Awair API access token",
        description=(
            "An Awair API access token. Can be obtained from "
            "https://developer.getawair.com/console/access-token."
        ),
    )
    device_id = fields.Integer(
        required=True,
        default=None,
        title="Device ID",
        description=(
            "The ID of the device to read data from. To find the device ID: "
            "`curl 'https://developer-apis.awair.is/v1/users/self/devices' "
            "-H 'Authorization: Bearer example-token'`"
        ),
    )
    device_type = fields.String(
        required=False,
        default="awair-element",
        title="Device type",
        description="The type of device to read data from.",
    )
    prefix = fields.String(
        required=False,
        default="hub.awair",
        title="The prefix for events from this source",
        description=(
            "The prefix for events from this source. For example, if the "
            "prefix is `awair` an event name `awair.score` will be emitted "
            "for the air quality score."
        ),
    )


@configuration_schema(AwairConfig())
async def awair(
    access_token: str,
    device_id: int,
    device_type: str = "awair-element",
    prefix: str = "hub.awair",
) -> Stream:
    """
    Fetch air quality data from Awair Element monitor.

    This source will periodically retrieve air quality data from
    an Awair Element monitor.
    """
    _logger.info("Fetching air quality data")
    url = (
        "https://developer-apis.awair.is/v1/users/self/devices/"
        f"{device_type}/{device_id}/air-data/latest?fahrenheit=false"
    )
    headers = {"Authorization": f"Bearer {access_token}"}
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers)
    payload = response.json()
    _logger.debug("Received %s", payload)

    for row in payload["data"]:
        timestamp = datetime.strptime(
            row["timestamp"],
            "%Y-%m-%dT%H:%M:%S.%fZ",
        ).replace(tzinfo=timezone.utc)
        yield {
            "timestamp": timestamp,
            "name": f"{prefix}.score",
            "value": row["score"],
        }

        for sensor in row["sensors"]:
            yield {
                "timestamp": timestamp,
                "name": f"{prefix}.{sensor['comp']}",
                "value": sensor["value"],
            }
