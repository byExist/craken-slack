# pyright: reportUnknownMemberType=false, reportUnknownArgumentType=false
# Scoped: slack_sdk's SlackResponse.get is loosely typed; the rest stays strict.
"""Translate Slack API errors into actionable, LLM-facing messages.

slack_sdk raises ``SlackApiError`` whenever Slack returns ``{"ok": false}``. For
permission/auth failures (missing scope, bad or wrong-type token) neither
retrying nor rephrasing helps, so we re-raise as a ``PermissionError`` telling
the model to stop and relay the gap to the user — the Slack analog of the
Atlassian client's 403 hook. Every other error is surfaced with its Slack error
code so the model can correct the call (e.g. ``channel_not_found``).
"""

from collections.abc import Callable
from typing import TypeVar

from slack_sdk.errors import SlackApiError

T = TypeVar("T")

# Slack error codes that mean the token/app lacks access — not fixable by retry.
_AUTH_ERRORS = frozenset(
    {
        "not_authed",
        "invalid_auth",
        "account_inactive",
        "token_revoked",
        "token_expired",
        "missing_scope",
        "not_allowed_token_type",
        "no_permission",
        "ekm_access_denied",
    }
)


def call(fn: Callable[[], T]) -> T:
    """Run a Slack Web API call, turning ``{"ok": false}`` into a clear error.

    A permission/auth error becomes a ``PermissionError`` instructing the model
    not to retry; any other Slack error becomes a ``RuntimeError`` carrying the
    Slack error code.
    """
    try:
        return fn()
    except SlackApiError as exc:
        error = str(exc.response.get("error", "unknown"))
        if error in _AUTH_ERRORS:
            raise PermissionError(
                f"Slack denied this call: '{error}'. The token lacks the required "
                f"scope or is invalid / the wrong type. Do not retry; tell the user "
                f"to reinstall the Slack app with the needed scope, or fix the token "
                f"via /plugin config slack. (Search needs a user token, xoxp-.)"
            ) from exc
        raise RuntimeError(f"Slack API error: '{error}'.") from exc
