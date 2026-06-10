"""Tests for slack.errors — translating SlackApiError into actionable errors."""

from typing import cast

import pytest
from slack_sdk.errors import SlackApiError
from slack_sdk.web import SlackResponse

from slack_mcp.errors import call


def _raise(exc: Exception) -> object:
    raise exc


def _api_error(error: str) -> SlackApiError:
    return SlackApiError("boom", response=cast(SlackResponse, {"error": error}))


def test_call_returns_value_on_success():
    assert call(lambda: 42) == 42


def test_auth_error_becomes_permission_error():
    with pytest.raises(PermissionError, match="missing_scope"):
        call(lambda: _raise(_api_error("missing_scope")))


def test_other_error_becomes_runtime_error():
    with pytest.raises(RuntimeError, match="channel_not_found"):
        call(lambda: _raise(_api_error("channel_not_found")))
