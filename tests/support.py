"""Test support: a stand-in for slack_sdk's SlackResponse.

The Slack client reads ``resp.data`` (the parsed JSON dict). ``FakeResponse``
exposes just that, so tests set a WebClient method's ``return_value`` to
``response({...})`` and let the real client parsing run. Lives outside conftest
so test modules can import it for annotations.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from slack_mcp.schema.channel import Channel
from slack_mcp.schema.user import User
from slack_mcp.schema.usergroup import Usergroup


@dataclass
class FakeResponse:
    """Minimal stand-in for SlackResponse: exposes ``.data`` and ``.headers``."""

    data: dict[str, Any]
    headers: dict[str, str] = field(default_factory=dict[str, str])


def response(
    data: dict[str, Any], headers: dict[str, str] | None = None
) -> FakeResponse:
    return FakeResponse(data) if headers is None else FakeResponse(data, headers)


# Minimal valid payloads for schemas with required fields — spread with **over to
# vary. Centralized here so a change to which fields are required is a one-line
# edit, not a sweep across every test fixture.


def profile(**over: Any) -> dict[str, Any]:
    return {
        "display_name": "",
        "real_name": "",
        "title": "",
        "status_text": "",
        "status_emoji": "",
        **over,
    }


def user(**over: Any) -> dict[str, Any]:
    return {"id": "U1", "name": "u1", "is_bot": False, "profile": profile(), **over}


def channel(**over: Any) -> dict[str, Any]:
    return {"id": "C1", "is_im": False, "created": 0, **over}


def message(**over: Any) -> dict[str, Any]:
    return {"type": "message", "text": "", "ts": "1.1", **over}


def usergroup(**over: Any) -> dict[str, Any]:
    return {
        "id": "S1",
        "team_id": "T1",
        "handle": "devs",
        "name": "Devs",
        "description": "",
        "is_external": False,
        "date_delete": 0,
        **over,
    }


# Model forms — for tests that patch a typed client function's return value
# (which yields models, not raw response dicts).


def channel_model(**over: Any) -> Channel:
    return Channel.model_validate(channel(**over))


def user_model(**over: Any) -> User:
    return User.model_validate(user(**over))


def usergroup_model(**over: Any) -> Usergroup:
    return Usergroup.model_validate(usergroup(**over))
