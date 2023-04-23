"""
Tests for the helper functions.
"""

import asyncio
import random

import aiotools
import pytest
import yaml
from marshmallow_jsonschema import JSONSchema

from senor_octopus.graph import build_dag
from senor_octopus.lib import (
    build_marshmallow_schema,
    flatten,
    merge_streams,
    render_dag,
)
from senor_octopus.sources.awair import awair


def test_flatten() -> None:
    """
    Test the ``flatten`` function.
    """
    assert flatten({"a": 1, "b": 2.0, "c": "foo", "d": {"e": "bar"}}) == {
        "a": 1,
        "b": 2.0,
        "c": "foo",
        "d.e": "bar",
    }


@pytest.mark.asyncio
async def test_render_dag(mock_config) -> None:
    """
    Test the ``render_dag`` function.
    """
    dag = build_dag(mock_config)
    assert (
        render_dag(dag, use_color=False).strip()
        == "*   random\n|\\  \n* | check\n| * normal\n* high"
    )


@pytest.mark.asyncio
async def test_render_dag_many_to_many() -> None:
    """
    Test ``render_dag`` function with a DAG that has many-to-many relationship.
    """
    config = yaml.load(
        """
one:
  plugin: source.random
  flow: -> two, three

two:
  plugin: filter.jsonpath
  flow: one -> four
  filter: $.events[?(@.value>0.5)]

three:
  plugin: filter.jsonpath
  flow: one -> four
  filter: $.events[?(@.value<=0.5)]

four:
  plugin: sink.log
  flow: two, three ->
        """,
        Loader=yaml.SafeLoader,
    )

    dag = build_dag(config)
    assert (
        render_dag(dag, use_color=False).strip()
        == "*   one\n|\\  \n* | three\n| * two\n|/  \n* four"
    )


@pytest.mark.asyncio
async def test_merge_streams() -> None:
    """
    Test the ``merge_streams`` function.
    """
    vclock = aiotools.VirtualClock()

    random.seed(42)

    async def gen(name, count, sleep):
        """
        Generate a stream of events.
        """
        for _ in range(count):
            await asyncio.sleep(sleep)
            yield (name, random.random())

    stream = gen("stream1", 3, 2)
    with vclock.patch_loop():
        events = [event async for event in stream]
    assert events == [
        ("stream1", 0.6394267984578837),
        ("stream1", 0.025010755222666936),
        ("stream1", 0.27502931836911926),
    ]

    stream = gen("stream2", 2, 5)
    with vclock.patch_loop():
        events = [event async for event in stream]
    assert events == [("stream2", 0.22321073814882275), ("stream2", 0.7364712141640124)]

    random.seed(42)
    stream = merge_streams(gen("stream1", 3, 2), gen("stream2", 2, 5))
    with vclock.patch_loop():
        events = [event async for event in stream]
    assert events == [
        ("stream1", 0.6394267984578837),
        ("stream1", 0.025010755222666936),
        ("stream2", 0.27502931836911926),
        ("stream1", 0.22321073814882275),
        ("stream2", 0.7364712141640124),
    ]


def test_build_marshmallow_schema() -> None:
    """
    Test the ``build_marshmallow_schema`` function.
    """
    json_schema = JSONSchema()
    schema = build_marshmallow_schema(awair)
    assert json_schema.dump(schema) == {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "definitions": {
            "GeneratedSchema": {
                "type": "object",
                "properties": {
                    "access_token": {"title": "access_token", "type": "string"},
                    "device_id": {"title": "device_id", "type": "integer"},
                    "device_type": {
                        "title": "device_type",
                        "type": "string",
                        "default": "awair-element",
                    },
                    "prefix": {
                        "title": "prefix",
                        "type": "string",
                        "default": "hub.awair",
                    },
                },
                "required": ["access_token", "device_id"],
                "additionalProperties": False,
            },
        },
        "$ref": "#/definitions/GeneratedSchema",
    }

    json_schema = JSONSchema()
    assert json_schema.dump(awair.configuration_schema) == {  # type: ignore
        "$schema": "http://json-schema.org/draft-07/schema#",
        "definitions": {
            "AwairConfig": {
                "required": ["access_token", "device_id"],
                "properties": {
                    "access_token": {
                        "title": "Awair API access token",
                        "type": "string",
                        "default": None,
                        "description": (
                            "An Awair API access token. Can be obtained from "
                            "https://developer.getawair.com/console/access-token."
                        ),
                    },
                    "device_id": {
                        "title": "Device ID",
                        "type": "integer",
                        "default": None,
                        "description": (
                            "The ID of the device to read data from. To find "
                            "the device ID: `curl "
                            "'https://developer-apis.awair.is/v1/users/self/devices' "
                            "-H 'Authorization: Bearer example-token'`"
                        ),
                    },
                    "device_type": {
                        "title": "Device type",
                        "type": "string",
                        "default": "awair-element",
                        "description": "The type of device to read data from.",
                    },
                    "prefix": {
                        "title": "The prefix for events from this source",
                        "type": "string",
                        "default": "hub.awair",
                        "description": (
                            "The prefix for events from this source. For example, if "
                            "the prefix is `awair` an event name `awair.score` will "
                            "be emitted for the air quality score."
                        ),
                    },
                },
                "type": "object",
                "additionalProperties": False,
            },
        },
        "$ref": "#/definitions/AwairConfig",
    }

    def some_func(arg: object) -> object:
        return arg

    with pytest.raises(TypeError) as excinfo:
        build_marshmallow_schema(some_func)  # type: ignore
    assert str(excinfo.value) == "Unsupported type <class 'object'> for parameter arg"
