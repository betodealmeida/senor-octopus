"""
Tests for the helper functions.
"""

import asyncio
import random

import aiotools
import pytest
import yaml

from senor_octopus.graph import build_dag
from senor_octopus.lib import flatten, merge_streams, render_dag


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
        == r"""
*   random
|\
* | check
| * normal
* high
        """.strip()
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
        == r"""
*   one
|\
* | three
| * two
|/
* four
        """.strip()
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
