# flake8: noqa
import pytest
from senor_octopus.cli import CaseConfigParser
from senor_octopus.graph import build_dag
from senor_octopus.lib import flatten
from senor_octopus.lib import render_dag


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
    config = CaseConfigParser()
    config.read_string(
        """
        [one]
        plugin = source.random
        flow = -> two, three

        [two]
        plugin = filter.jsonpath
        flow = one -> four
        filter = $.events[?(@.value>0.5)]

        [three]
        plugin = filter.jsonpath
        flow = one -> four
        filter = $.events[?(@.value<=0.5)]

        [four]
        plugin = sink.log
        flow = two, three ->
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
