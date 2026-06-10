"""Tests for slack.config — settings loaded from SLACK_* env vars."""

import os

import pytest
from pydantic import ValidationError
from pytest_mock import MockerFixture

from slack_mcp.config import Auth, get_auth

_CREDS = {"SLACK_TOKEN": "xoxb-secret"}


def test_auth_reads_token_from_env(mocker: MockerFixture):
    mocker.patch.dict(os.environ, _CREDS)

    auth = Auth()  # type: ignore[call-arg]

    assert auth.token.get_secret_value() == "xoxb-secret"


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
    get_auth.cache_clear()

    assert get_auth() is get_auth()
