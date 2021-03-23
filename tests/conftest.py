"""
    Dummy conftest.py for senor_octopus.

    If you don't know what this is for, just leave it empty.
    Read more about conftest.py under:
    - https://docs.pytest.org/en/stable/fixture.html
    - https://docs.pytest.org/en/stable/writing_plugins.html
"""
import pytest
from senor_octopus.cli import CaseConfigParser
from senor_octopus.graph import build_dag


config_content = """
[random]
plugin = source.random
flow = -> check, normal
schedule = * * * * *

[check]
plugin = filter.jsonpath
flow = random -> high
filter = $.events[?(@.value>0.5)]

[normal]
plugin = sink.log
flow = random ->

[high]
plugin = sink.log
flow = check ->
throttle = 5 minutes
level = warning
"""


@pytest.fixture
def mock_config():
    config = CaseConfigParser()
    config.read_string(config_content)
    yield config


@pytest.fixture
def mock_dag(mock_config):
    dag = build_dag(mock_config)
    yield dag
