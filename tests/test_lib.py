import pytest
from senor_octopus.lib import flatten
from senor_octopus.lib import render_dag


def test_flatten() -> None:
    assert flatten({"a": 1, "b": 2.0, "c": "foo", "d": {"e": "bar"}}) == {
        "a": 1,
        "b": 2.0,
        "c": "foo",
        "d.e": "bar",
    }


@pytest.mark.asyncio
async def test_render_dag(mock_dag) -> None:
    assert (
        render_dag(mock_dag, use_color=False)
        == "*   random\n|\\  \n* | check\n| * normal\n* high\n"
    )
