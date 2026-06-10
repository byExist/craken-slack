"""File schemas."""

from slack_mcp.schema.base import SlackModel


class File(SlackModel):
    """A shared file. Slack API: the ``file`` object from files.info."""

    id: str | None = None
    name: str | None = None
    title: str | None = None
    mimetype: str | None = None
    filetype: str | None = None
    pretty_type: str | None = None
    user: str | None = None
    size: int | None = None
    url_private: str | None = None
    url_private_download: str | None = None
    permalink: str | None = None
    permalink_public: str | None = None
    created: int | None = None
    is_external: bool | None = None
    preview: str | None = None
