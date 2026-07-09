"""Message schemas."""

from typing import Any

from pydantic import ConfigDict, SerializerFunctionWrapHandler, model_serializer

from slack_mcp.schema.base import SlackModel, keep_present
from slack_mcp.schema.channel import ResponseMetadata
from slack_mcp.schema.file import File
from slack_mcp.schema.user import UserProfileShort


class Reaction(SlackModel):
    """A reaction on a message. Slack also returns the reactor IDs (``users``),
    dropped here to keep history compact — ``count`` is the signal."""

    name: str
    count: int


# Known noise dropped from output (see Message). Conservative: when a field's
# status is unclear it is left OUT (kept) — a wrongly dropped field is silent
# content loss, a stray kept one is only verbose.
_BLOAT: frozenset[str] = frozenset(
    {
        "client_msg_id",
        "team",
        "source_team",
        "user_team",
        "app_id",
        "icons",  # bot avatar urls
        "bot_profile",  # nested bot blob, redundant with bot_id/username
        "display_as_bot",
        "is_intro",
        "is_starred",
        "is_delayed_message",
        "last_read",  # per-viewer read state
        "unread_count",
        "latest_reply",  # reply_count is the signal
        "reply_users",  # reply_users_count is the signal (kept raw)
        "pinned_to",
        "subscribed",
        "upload",
    }
)


class Message(SlackModel):
    """A message in a conversation.

    Slack API: a ``messages[]`` item from conversations.history / .replies.

    Polymorphic (subtype / bot / Block Kit) and evolving, so the model is *open*
    (``extra="allow"``): declared fields are the curated signal, undeclared ones
    survive as raw, and ``_BLOAT`` drops only known noise. This default-keep +
    denylist (unlike the closed models' default-drop) is what stops bot content
    in ``blocks`` / ``attachments`` and subtype payloads from being silently lost.
    """

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    @model_serializer(mode="wrap")
    def _drop_none(self, handler: SerializerFunctionWrapHandler) -> dict[str, Any]:
        """Base absence rule (``keep_present``) plus: drop ``_BLOAT`` — known
        noise that ``extra="allow"`` would otherwise keep raw. Lives here, not on
        the base, because Message is the only open model; closed models curate by
        declaring only what they keep, so they need no denylist."""
        return keep_present((k, v) for k, v in handler(self).items() if k not in _BLOAT)

    type: str
    subtype: str | None = None
    user: str | None = None
    user_profile: UserProfileShort | None = None
    bot_id: str | None = None
    username: str | None = None  # display name a bot/app posts under
    # spec-required but defaulted so a text-less variant still parses; "" kept.
    text: str = ""
    # Bot/app content lives here (``text`` often empty). Raw passthrough: the spec
    # calls ``blocks`` "a very loose definition", has no attachment schema, and
    # Block Kit is a wide, evolving union no static model captures.
    blocks: list[dict[str, Any]] | None = None
    attachments: list[dict[str, Any]] | None = None
    files: list[File] | None = None
    reactions: list[Reaction] | None = None
    # Content of system-subtype messages:
    topic: str | None = None  # channel_topic
    purpose: str | None = None  # channel_purpose
    name: str | None = None  # channel_name (new)
    old_name: str | None = None  # channel_name (previous)
    ts: str
    thread_ts: str | None = None
    reply_count: int | None = None


class MessageList(SlackModel):
    """conversations.history / conversations.replies result."""

    messages: list[Message] = []
    has_more: bool | None = None
    response_metadata: ResponseMetadata | None = None


class PostedMessage(SlackModel):
    """chat.postMessage / chat.update result."""

    channel: str
    ts: str
    message: Message


class Permalink(SlackModel):
    """chat.getPermalink result."""

    channel: str
    permalink: str
