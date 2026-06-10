"""Channel (conversation) schemas."""

from slack_mcp.schema.base import SlackModel


class ResponseMetadata(SlackModel):
    """Cursor-pagination metadata shared by Slack list endpoints."""

    next_cursor: str | None = None


class ChannelText(SlackModel):
    """A channel's topic or purpose. Slack returns ``{value, creator, last_set}``;
    only the text ``value`` is kept."""

    value: str | None = None


class Channel(SlackModel):
    """A Slack conversation: channel, group, or DM.

    Slack API: the ``channel`` object from conversations.* endpoints.
    """

    id: str | None = None
    name: str | None = None
    is_channel: bool | None = None
    is_private: bool | None = None
    is_archived: bool | None = None
    is_im: bool | None = None
    num_members: int | None = None
    topic: ChannelText | None = None
    purpose: ChannelText | None = None
    created: int | None = None


class ChannelList(SlackModel):
    """conversations.list result."""

    channels: list[Channel] = []
    response_metadata: ResponseMetadata | None = None
