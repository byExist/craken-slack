"""Tests for slack.config — the token secret and the optional runtime settings."""

import os

import pytest
from pydantic import ValidationError
from pytest_mock import MockerFixture

from slack_mcp.config import Auth, Claude, Slack, get_auth, get_claude, get_slack

_CREDS = {"SLACK_TOKEN": "xoxb-secret"}


def test_auth_reads_token_from_env(mocker: MockerFixture):
    mocker.patch.dict(os.environ, _CREDS)

    assert Auth().token.get_secret_value() == "xoxb-secret"  # type: ignore[call-arg]


def test_auth_token_is_masked_in_repr(mocker: MockerFixture):
    mocker.patch.dict(os.environ, _CREDS)

    auth = Auth()  # type: ignore[call-arg]

    assert "xoxb-secret" not in repr(auth)
    assert "xoxb-secret" not in str(auth.token)


def test_auth_requires_token():
    # isolate_env has cleared SLACK_* — construction must fail, not guess.
    with pytest.raises(ValidationError):
        Auth()  # type: ignore[call-arg]


def test_get_auth_is_cached(mocker: MockerFixture):
    mocker.patch.dict(os.environ, _CREDS)

    assert get_auth() is get_auth()


def test_cache_ttl_default_and_override(mocker: MockerFixture):
    assert Slack().cache_ttl == 3600.0  # default

    mocker.patch.dict(os.environ, {"SLACK_CACHE_TTL": "30"})
    assert Slack().cache_ttl == 30.0


def test_cache_ttl_bad_or_negative_falls_back(mocker: MockerFixture):
    mocker.patch.dict(os.environ, {"SLACK_CACHE_TTL": "abc"})
    assert Slack().cache_ttl == 3600.0  # unparseable → default

    mocker.patch.dict(os.environ, {"SLACK_CACHE_TTL": "-5"})
    assert Slack().cache_ttl == 3600.0  # negative → default


def test_claude_plugin_data_from_env(mocker: MockerFixture):
    assert Claude().plugin_data is None  # isolate_env cleared it

    mocker.patch.dict(os.environ, {"CLAUDE_PLUGIN_DATA": "/tmp/pd"})
    assert Claude().plugin_data == "/tmp/pd"


def test_runtime_getters_cached_without_token(mocker: MockerFixture):
    # No SLACK_TOKEN set — building the runtime settings must not require it.
    mocker.patch.dict(os.environ, {"SLACK_CACHE_TTL": "42", "CLAUDE_PLUGIN_DATA": "/p"})

    assert get_slack() is get_slack()  # lru_cached singletons
    assert get_claude() is get_claude()
    assert get_slack().cache_ttl == 42.0
    assert get_claude().plugin_data == "/p"
