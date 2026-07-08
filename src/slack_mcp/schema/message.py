"""Message schemas."""

from slack_mcp.schema.base import SlackModel
from slack_mcp.schema.channel import ResponseMetadata
from slack_mcp.schema.file import File
from slack_mcp.schema.user import UserProfileShort


class Reaction(SlackModel):
    """A reaction on a message. Slack also returns the reactor IDs (``users``),
    dropped here to keep history compact — ``count`` is the signal."""

    name: str
    count: int


class Message(SlackModel):
    """A message in a conversation.

    Slack API: a ``messages[]`` item from conversations.history / .replies.
    """

    type: str
    subtype: str | None = None
    user: str | None = None
    user_profile: UserProfileShort | None = None
    bot_id: str | None = None
    text: str
    ts: str
    thread_ts: str | None = None
    reply_count: int | None = None
    reactions: list[Reaction] | None = None
    files: list[File] | None = None


class MessageList(SlackModel):
    """conversations.history / conversations.replies result."""

    messages: list[Message] = []
    has_more: bool | None = None
    response_metadata: ResponseMetadata | None = None


class PostedMessage(SlackModel):
    """chat.postMessage / chat.update result."""

    channel: str | None = None
    ts: str | None = None
    message: Message | None = None


class Permalink(SlackModel):
    """chat.getPermalink result."""

    channel: str | None = None
    permalink: str | None = None
