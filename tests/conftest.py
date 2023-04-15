"""
Pytest configuration.
"""

import pytest
import yaml

CONFIG_CONTENT = """
random:
  plugin: source.random
  flow: -> check, normal
  schedule: "* * * * *"

check:
  plugin: filter.jsonpath
  flow: random -> high
  filter: $.events[?(@.value>0.5)]

normal:
  plugin: sink.log
  flow: random ->

high:
  plugin: sink.log
  flow: check ->
  throttle: 5 minutes
  level: warning
"""


@pytest.fixture
def mock_config():
    """
    Mock config for testing.
    """
    yield yaml.load(CONFIG_CONTENT, Loader=yaml.SafeLoader)
