"""Message schemas."""

from slack_mcp.schema.base import SlackModel
from slack_mcp.schema.channel import ResponseMetadata


class Reaction(SlackModel):
    """A reaction on a message. Slack also returns the reactor IDs (``users``),
    dropped here to keep history compact — ``count`` is the signal."""

    name: str | None = None
    count: int | None = None


class Message(SlackModel):
    """A message in a conversation.

    Slack API: a ``messages[]`` item from conversations.history / .replies.
    """

    type: str | None = None
    subtype: str | None = None
    user: str | None = None
    bot_id: str | None = None
    text: str | None = None
    ts: str | None = None
    thread_ts: str | None = None
    reply_count: int | None = None
    reactions: list[Reaction] | None = None


class MessageList(SlackModel):
    """conversations.history / conversations.replies result."""

    messages: list[Message] = []
    has_more: bool | None = None
    response_metadata: ResponseMetadata | None = None


class PostedMessage(SlackModel):
    """chat.postMessage / chat.update result."""

    ok: bool | None = None
    channel: str | None = None
    ts: str | None = None
    message: Message | None = None


class Permalink(SlackModel):
    """chat.getPermalink result."""

    ok: bool | None = None
    channel: str | None = None
    permalink: str | None = None
