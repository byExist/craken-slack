"""Search schemas."""

from slack_mcp.schema.base import SlackModel
from slack_mcp.schema.channel import Channel, ResponseMetadata


class SearchMatch(SlackModel):
    """A single hit from search.messages."""

    type: str | None = None
    user: str | None = None
    username: str | None = None
    text: str | None = None
    ts: str | None = None
    channel: Channel | None = None
    permalink: str | None = None


class SearchMessages(SlackModel):
    """The ``messages`` block of a search.messages result."""

    total: int | None = None
    matches: list[SearchMatch] = []


class SearchResult(SlackModel):
    """search.messages result."""

    query: str | None = None
    messages: SearchMessages | None = None
    response_metadata: ResponseMetadata | None = None
