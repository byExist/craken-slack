"""In-memory name → ID resolution for channels, users, and usergroups.

Slack tools take IDs (``C0123…`` / ``U0123…``), but people — and the model —
refer to ``#general`` or ``@alice``. This layer resolves a name or handle to an
ID, lazily caching the workspace's listings in memory on first use. Unlike
heavier servers it is **not** disk-persisted or boot-warmed, which keeps the
plugin light; the cost is one listing fetch on the first lookup of a session.

Two uses:

* ``resolve_channel`` / ``resolve_user`` — for an explicit tool argument: an ID
  passes through; a name is looked up (cache refreshed once on a miss), and a
  clear error is raised if it still isn't found.
* ``substitute_mentions`` — for free-form message text: rewrites ``@handle`` /
  ``#channel`` / ``@here`` etc. to Slack tokens, leaving anything that doesn't
  resolve as literal text (so over-matching is harmless), and never touching
  code, links, or already-encoded ``<…>`` tokens.
"""

import re
from collections.abc import Callable

from slack_mcp import client

# Slack IDs are uppercase; channel/user names and handles are lowercase, so the
# two never collide. Channels: C (public), G (private/group), D (DM). Users:
# U (member), W (Enterprise Grid member).
_CHANNEL_ID = re.compile(r"[CDG][A-Z0-9]+")
_USER_ID = re.compile(r"[UW][A-Z0-9]+")

_channels: dict[str, str] | None = None  # name -> channel id
_users: dict[str, str] | None = None  # handle -> user id
_usergroups: dict[str, str] | None = None  # handle -> subteam id


def _build_channels() -> dict[str, str]:
    table: dict[str, str] = {}
    cursor: str | None = None
    while True:
        page = client.list_channels(
            types="public_channel,private_channel", limit=200, cursor=cursor
        )
        for ch in page.channels:
            if ch.name and ch.id:
                table[ch.name] = ch.id
        cursor = page.response_metadata.next_cursor if page.response_metadata else None
        if not cursor:
            return table


def _build_users() -> dict[str, str]:
    table: dict[str, str] = {}
    cursor: str | None = None
    while True:
        page = client.list_users(limit=200, cursor=cursor)
        for member in page.members:
            if member.name and member.id:
                table[member.name] = member.id
        cursor = page.response_metadata.next_cursor if page.response_metadata else None
        if not cursor:
            return table


def _build_usergroups() -> dict[str, str]:
    table: dict[str, str] = {}
    for group in client.list_usergroups().usergroups:
        if group.handle and group.id:
            table[group.handle] = group.id
    return table


def resolve_channel(ref: str) -> str:
    """Resolve a channel reference (ID, ``#name``, or ``name``) to a channel ID."""
    global _channels  # noqa: PLW0603
    if _CHANNEL_ID.fullmatch(ref):
        return ref
    name = ref.lstrip("#")
    table = _channels
    if table is None:
        table = _build_channels()
    elif name not in table:
        table = _build_channels()  # warm but missing — maybe newly created
    _channels = table
    if name not in table:
        raise ValueError(
            f"channel '{ref}' not found — pass a channel ID (C…) or check list_channels."
        )
    return table[name]


def resolve_user(ref: str) -> str:
    """Resolve a user reference (ID, ``@handle``, or ``handle``) to a user ID."""
    global _users  # noqa: PLW0603
    if _USER_ID.fullmatch(ref):
        return ref
    handle = ref.lstrip("@")
    table = _users
    if table is None:
        table = _build_users()
    elif handle not in table:
        table = _build_users()
    _users = table
    if handle not in table:
        raise ValueError(
            f"user '{ref}' not found — pass a user ID (U…) or check list_users."
        )
    return table[handle]


# ---------------------------------------------------------------------------
# In-text mention substitution
# ---------------------------------------------------------------------------

_SPECIAL = frozenset({"here", "channel", "everyone"})

# A leading word char before @/# means it isn't a mention (emails, C#, issue#42).
# Channel names/handles are lowercase, but accept any case and fold for lookup.
_AT = re.compile(r"(?<![\w@/])@([A-Za-z0-9][\w.-]*)")
_HASH = re.compile(r"(?<![\w#/])#([A-Za-z0-9][\w.-]*)")

# Regions masked before substitution so their @/# are never rewritten.
_MASKS = (
    re.compile(r"```.*?```", re.DOTALL),  # fenced code
    re.compile(r"`[^`]+`"),  # inline code
    re.compile(r"\[[^\]]*\]\([^)]+\)"),  # markdown links
    re.compile(r"<[^>]+>"),  # existing <@…>/<#…>/<!…>/<url|text> tokens
)


def _channel_table() -> dict[str, str]:
    global _channels  # noqa: PLW0603
    if _channels is None:
        _channels = _build_channels()
    return _channels


def _user_table() -> dict[str, str]:
    global _users  # noqa: PLW0603
    if _users is None:
        _users = _build_users()
    return _users


def _usergroup_table() -> dict[str, str]:
    global _usergroups  # noqa: PLW0603
    if _usergroups is None:
        _usergroups = _build_usergroups()
    return _usergroups


def _safe_table(getter: Callable[[], dict[str, str]]) -> dict[str, str]:
    """Build a lookup table, best-effort — a listing that fails (e.g. a missing
    scope) yields an empty table so that type simply isn't resolved."""
    try:
        return getter()
    except Exception:
        return {}


def substitute_mentions(text: str) -> str:
    """Rewrite ``@handle`` / ``#channel`` / ``@here`` etc. to Slack tokens.

    Code, links, and existing ``<…>`` tokens are masked first; names that don't
    resolve are left as literal text. Only the listings actually referenced are
    fetched, so plain messages cost nothing.
    """
    store: list[str] = []

    def _stash(m: re.Match[str]) -> str:
        store.append(m.group(0))
        return f"\x00{len(store) - 1}\x00"

    masked = text
    for pattern in _MASKS:
        masked = pattern.sub(_stash, masked)

    if _AT.search(masked):
        users = _safe_table(_user_table)
        groups = _safe_table(_usergroup_table)

        def _at(m: re.Match[str]) -> str:
            handle = m.group(1).lower()
            if handle in _SPECIAL:
                return f"<!{handle}>"
            if handle in users:
                return f"<@{users[handle]}>"
            if handle in groups:
                return f"<!subteam^{groups[handle]}>"
            return m.group(0)

        masked = _AT.sub(_at, masked)

    if _HASH.search(masked):
        channels = _safe_table(_channel_table)

        def _hash(m: re.Match[str]) -> str:
            name = m.group(1).lower()
            if name in channels:
                return f"<#{channels[name]}>"
            return m.group(0)

        masked = _HASH.sub(_hash, masked)

    for index, original in enumerate(store):
        masked = masked.replace(f"\x00{index}\x00", original)
    return masked


def reset() -> None:
    """Clear the in-memory caches (used to isolate tests)."""
    global _channels, _users, _usergroups  # noqa: PLW0603
    _channels = None
    _users = None
    _usergroups = None
