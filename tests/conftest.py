"""Shared test fixtures.

The Slack client is a lazy ``WebClient`` singleton. Tests never hit the network:
the fixtures here clear ``SLACK_*`` env vars (autouse) so a stray call fails
loudly, reset the client singleton and the name cache between tests, and install
a ``MagicMock(spec=WebClient)`` as the client so tests set per-method return
values and assert call args. All patching goes through pytest-mock's ``mocker``.
"""

import os
from unittest.mock import MagicMock

import pytest
from pytest_mock import MockerFixture
from slack_sdk import WebClient

from slack_mcp import cache, capabilities
from slack_mcp import client as slack_client
from slack_mcp.config import get_auth, get_claude, get_slack


@pytest.fixture(autouse=True)
def isolate_env(mocker: MockerFixture) -> None:
    """Strip real Slack config and reset the singleton + caches each test."""
    mocker.patch.dict(os.environ)  # snapshot; restored after the test
    os.environ.pop("SLACK_TOKEN", None)
    os.environ.pop("CLAUDE_PLUGIN_DATA", None)  # default to in-memory; no disk writes
    os.environ.pop("SLACK_CACHE_TTL", None)
    get_auth.cache_clear()
    get_slack.cache_clear()
    get_claude.cache_clear()
    cache.reset()
    capabilities.reset()
    mocker.patch.object(slack_client, "_client", None)


@pytest.fixture
def slack_api(mocker: MockerFixture) -> MagicMock:
    """A MagicMock(spec=WebClient) installed as the Slack client singleton, with a
    fake token in the env so ``get_auth().token`` resolves."""
    mocker.patch.dict(os.environ, {"SLACK_TOKEN": "xoxb-test"})
    fake = mocker.MagicMock(spec=WebClient)
    mocker.patch.object(slack_client, "_client", None)

    def _factory(token: str) -> MagicMock:
        return fake

    mocker.patch.object(slack_client, "WebClient", _factory)
    return fake
