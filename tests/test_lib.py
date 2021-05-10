# flake8: noqa
import asyncio
import random

import aiotools
import pytest
import yaml
from senor_octopus.graph import build_dag
from senor_octopus.lib import flatten
from senor_octopus.lib import merge_streams
from senor_octopus.lib import render_dag
from senor_octopus.sources.rand import rand


def test_flatten() -> None:
    assert flatten({"a": 1, "b": 2.0, "c": "foo", "d": {"e": "bar"}}) == {
        "a": 1,
        "b": 2.0,
        "c": "foo",
        "d.e": "bar",
    }


def test_render_dag(mock_dag) -> None:
    assert (
        render_dag(mock_dag, use_color=False).strip()
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
    vclock = aiotools.VirtualClock()

    random.seed(42)

    async def gen(name, count, sleep):
        for i in range(count):
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
