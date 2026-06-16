"""Tool availability from the token's granted OAuth scopes.

Slack enforces permissions via OAuth scopes server-side and reports the token's
granted scopes in the ``X-OAuth-Scopes`` response header. We read that once (an
``auth.test`` probe on first use, cached) and annotate any tool whose required
scope the token lacks — so the model is told not to attempt a call that would
fail with ``missing_scope``, and which scope to grant. Scopes are the real,
server-enforced gate, so the tool surface tracks them; there is no config gate.

Detection degrades to "no annotation" when scopes can't be determined (no token,
network error, or an absent header), so calls just fall back to the runtime error
path. Only unambiguous scope mappings are listed; an unmapped tool (e.g.
``auth.test``, ``chat.getPermalink``) is never annotated. Mirrors the role of
``atlassian.jira.permissions.describe``.
"""

import logging
from collections.abc import Callable
from functools import lru_cache
from typing import Any

from slack_mcp import client

logger = logging.getLogger(__name__)

# Scope sets where any one member authorizes the method — Slack picks the
# required *.read / *.history scope by channel type.
_READ = frozenset({"channels:read", "groups:read", "im:read", "mpim:read"})
_HISTORY = frozenset(
    {"channels:history", "groups:history", "im:history", "mpim:history"}
)

# Tool fn name -> scopes that allow it (any one suffices). Unmapped tools are
# never annotated. Kept to unambiguous mappings, so a tool is flagged only when
# the token definitely holds none of the scopes it could use.
_TOOL_SCOPES: dict[str, frozenset[str]] = {
    "list_channels": _READ,
    "get_channel": _READ,
    "get_channel_history": _HISTORY,
    "get_thread_replies": _HISTORY,
    "list_users": frozenset({"users:read"}),
    "get_user": frozenset({"users:read"}),
    "get_file": frozenset({"files:read"}),
    "download_file": frozenset({"files:read"}),
    "search_messages": frozenset({"search:read"}),
    "post_message": frozenset({"chat:write"}),
    "update_message": frozenset({"chat:write"}),
    "delete_message": frozenset({"chat:write"}),
    "add_reaction": frozenset({"reactions:write"}),
    "remove_reaction": frozenset({"reactions:write"}),
}


@lru_cache(maxsize=1)
def _granted() -> frozenset[str] | None:
    """The token's granted scopes, probed once; None if undeterminable."""
    try:
        return client.granted_scopes()
    except Exception:
        logger.debug("scope probe failed; skipping scope annotations")
        return None


def describe(fn: Callable[..., Any]) -> str:
    """Return ``fn``'s docstring, appending an Unavailable note when the token's
    granted scopes include none of the scopes ``fn`` requires."""
    doc = (fn.__doc__ or "").rstrip()
    required = _TOOL_SCOPES.get(fn.__name__)
    granted = _granted()
    if required and granted is not None and granted.isdisjoint(required):
        need = " or ".join(f"`{s}`" for s in sorted(required))
        return (
            f"{doc}\n\n"
            f"Unavailable: the token lacks the scope this needs ({need}); the "
            f"call will fail. Do not call it — tell the user to add it and "
            f"reinstall the app."
        )
    return doc


def reset() -> None:
    """Clear the cached scope probe (used to isolate tests)."""
    _granted.cache_clear()
