"""Slack MCP tools — pure functions, registered by server.py.

Thin wrappers over ``client``. Channel and user arguments accept an ID or a name
(``#general`` / ``@alice``); message text is standard Markdown (sent via Slack's
``markdown_text``), with ``@handle`` / ``#channel`` / ``@here`` rewritten to
Slack mention tokens by ``cache``.
"""

from typing import Annotated, Literal, TypeAlias

from pydantic import Field

from slack_mcp import cache, client, files
from slack_mcp.schema.auth import AuthTest
from slack_mcp.schema.channel import Channel, ChannelList
from slack_mcp.schema.file import File
from slack_mcp.schema.message import MessageList, Permalink, PostedMessage
from slack_mcp.schema.search import SearchResult
from slack_mcp.schema.user import User, UserList

# Common parameter annotations — keep per-tool signatures terse.
ChannelId: TypeAlias = Annotated[
    str,
    Field(
        description="Channel ID (C0123ABCD) or name (#general); names resolved via list_channels."
    ),
]
Timestamp: TypeAlias = Annotated[
    str, Field(description='Message timestamp ("ts"), e.g. 1700000000.000100.')
]
Limit: TypeAlias = Annotated[int, Field(description="Max results per page.")]
Cursor: TypeAlias = Annotated[
    str | None,
    Field(description="Pagination cursor from a prior response (next_cursor)."),
]
Oldest: TypeAlias = Annotated[
    str | None,
    Field(description="Only replies after this ts, exclusive (e.g. 1700000000.000100)."),
]
Emoji: TypeAlias = Annotated[
    str, Field(description="Emoji name without colons, e.g. thumbsup.")
]

# Success sentinel so void operations return something explicit, not empty.
Ok: TypeAlias = Literal["ok"]


# --- Identity ---


def get_current_user() -> AuthTest:
    """Get the authenticated identity (auth.test) — user/bot and workspace."""
    return client.get_current_user()


# --- Channels ---


def list_channels(
    types: Annotated[
        str,
        Field(
            description="Comma-separated: public_channel, private_channel, mpim, im."
        ),
    ] = "public_channel",
    limit: Limit = 100,
    cursor: Cursor = None,
) -> ChannelList:
    """List conversations (channels). Use get_channel for one you know by ID."""
    return client.list_channels(types=types, limit=limit, cursor=cursor)


def get_channel(channel_id: ChannelId) -> Channel:
    """Get a channel's metadata (name, topic, purpose, membership)."""
    return client.get_channel(cache.resolve_channel(channel_id))


def get_channel_history(
    channel_id: ChannelId,
    limit: Limit = 100,
    cursor: Cursor = None,
) -> MessageList:
    """Get recent messages in a channel, newest first."""
    return client.get_channel_history(
        cache.resolve_channel(channel_id), limit=limit, cursor=cursor
    )


def get_thread_replies(
    channel_id: ChannelId,
    thread_ts: Annotated[str, Field(description="ts of the thread's parent message.")],
    oldest: Oldest = None,
    limit: Limit = 100,
    cursor: Cursor = None,
) -> MessageList:
    """Get the replies in a thread. The parent message is always included first."""
    return client.get_thread_replies(
        cache.resolve_channel(channel_id),
        thread_ts,
        oldest=oldest,
        limit=limit,
        cursor=cursor,
    )


def join_channel(channel_id: ChannelId) -> Channel:
    """Join a public channel so its history can be read (adds the bot as a member)."""
    return client.join_channel(cache.resolve_channel(channel_id))


def open_dm(
    users: Annotated[
        str,
        Field(
            description="User ID(s) (U0123ABCD) or @handle(s), comma-separated; opens a DM (or group DM). Post to the returned channel id."
        ),
    ],
) -> Channel:
    """Open a direct message with one or more users; returns the DM channel to post to."""
    resolved = ",".join(cache.resolve_user(u.strip()) for u in users.split(","))
    return client.open_dm(resolved)


# --- Messages ---


def get_permalink(channel_id: ChannelId, ts: Timestamp) -> Permalink:
    """Get a permanent link URL to a specific message."""
    return client.get_permalink(cache.resolve_channel(channel_id), ts)


# --- Users ---


def list_users(limit: Limit = 100, cursor: Cursor = None) -> UserList:
    """List workspace users."""
    return client.list_users(limit=limit, cursor=cursor)


def get_user(
    user_id: Annotated[
        str,
        Field(
            description="User ID (U0123ABCD) or @handle; handles resolved via list_users."
        ),
    ],
) -> User:
    """Get a user's profile."""
    return client.get_user(cache.resolve_user(user_id))


# --- Search ---


def search_messages(
    query: Annotated[str, Field(description="Slack search query.")],
    limit: Limit = 20,
    cursor: Cursor = None,
) -> SearchResult:
    """Search messages. Requires a user token (xoxp-); bot tokens cannot search."""
    return client.search_messages(query, count=limit, cursor=cursor)


# --- Files ---


def get_file(
    file_id: Annotated[str, Field(description="File ID (F0123ABCD).")],
) -> File:
    """Get a shared file's metadata — name, type, size, and download URL."""
    return client.get_file(file_id)


def download_file(
    file_id: Annotated[str, Field(description="File ID (F0123ABCD).")],
) -> str:
    """Download a shared file to a local temp path; returns the saved path."""
    data, content_type = client.download_file(file_id)
    return files.write_temp(data, content_type)


# --- Write ---


def post_message(
    channel: ChannelId,
    text: Annotated[
        str,
        Field(
            description="Message text (Markdown). @handle / #channel become mentions."
        ),
    ],
    thread_ts: Annotated[
        str | None,
        Field(description="Reply within this thread's ts; omit for a top-level post."),
    ] = None,
) -> PostedMessage:
    """Post a message to a channel, or reply in a thread."""
    return client.post_message(
        cache.resolve_channel(channel),
        cache.substitute_mentions(text),
        thread_ts=thread_ts,
    )


def update_message(
    channel: ChannelId,
    ts: Timestamp,
    text: Annotated[
        str,
        Field(
            description="New message text (Markdown). @handle / #channel become mentions."
        ),
    ],
) -> PostedMessage:
    """Edit a message you posted."""
    return client.update_message(
        cache.resolve_channel(channel), ts, cache.substitute_mentions(text)
    )


def delete_message(channel: ChannelId, ts: Timestamp) -> Ok:
    """Delete a message."""
    client.delete_message(cache.resolve_channel(channel), ts)
    return "ok"


def add_reaction(channel: ChannelId, ts: Timestamp, name: Emoji) -> Ok:
    """Add an emoji reaction to a message."""
    client.add_reaction(cache.resolve_channel(channel), ts, name)
    return "ok"


def remove_reaction(channel: ChannelId, ts: Timestamp, name: Emoji) -> Ok:
    """Remove an emoji reaction from a message."""
    client.remove_reaction(cache.resolve_channel(channel), ts, name)
    return "ok"
