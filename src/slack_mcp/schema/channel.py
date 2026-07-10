"""Channel (conversation) schemas."""

from slack_mcp.schema.base import SlackModel


class ResponseMetadata(SlackModel):
    """Cursor-pagination metadata shared by Slack list endpoints."""

    next_cursor: str | None = None


class ChannelText(SlackModel):
    """A channel's topic or purpose. Slack returns ``{value, creator, last_set}``;
    only the text ``value`` is kept."""

    value: str


class Channel(SlackModel):
    """A Slack conversation: channel, group, mpim, or DM.

    Slack API: ``objs_conversation`` (a variant union) from conversations.*, kept
    flat — a Pydantic union breaks the whole parse on any unseen shape.
    """

    id: str
    name: str | None = None
    is_channel: bool | None = None
    is_private: bool | None = None
    is_archived: bool | None = None
    is_im: bool
    is_mpim: bool | None = None  # group DM vs private channel
    num_members: int | None = None
    topic: ChannelText | None = None
    purpose: ChannelText | None = None
    user: str | None = None  # DM partner (IM variant)
    created: int | None = None  # omitted by search.messages


class ChannelList(SlackModel):
    """conversations.list result."""

    channels: list[Channel] = []
    response_metadata: ResponseMetadata | None = None
