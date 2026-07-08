"""Test support: a stand-in for slack_sdk's SlackResponse.

The Slack client reads ``resp.data`` (the parsed JSON dict). ``FakeResponse``
exposes just that, so tests set a WebClient method's ``return_value`` to
``response({...})`` and let the real client parsing run. Lives outside conftest
so test modules can import it for annotations.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


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
