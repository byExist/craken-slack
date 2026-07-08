"""User schemas."""

from slack_mcp.schema.base import SlackModel
from slack_mcp.schema.channel import ResponseMetadata


class Profile(SlackModel):
    """A user's profile — the useful subset of Slack's large profile object.

    Slack's full profile carries many avatar sizes (image_24…1024), custom
    fields, phone, etc.; only these few are kept so user lists stay compact.
    """

    display_name: str | None = None
    real_name: str | None = None
    title: str | None = None
    status_text: str | None = None
    status_emoji: str | None = None
    email: str | None = None


class UserProfileShort(SlackModel):
    """The compact profile Slack inlines on a message's ``user_profile``.

    Slack API: ``objs_user_profile_short`` — the author's identity carried on a
    message, so a reader can tell *who* spoke without a separate users.info
    lookup. Distinct from ``Profile`` (the fuller users.info object); only the
    naming subset is kept. These three are ``required`` in the spec, so — when
    ``user_profile`` is present at all — they are always set.
    """

    name: str
    real_name: str
    display_name: str


class User(SlackModel):
    """A Slack user.

    Slack API: the ``user`` / ``members[]`` object from users.info / users.list.
    """

    id: str | None = None
    name: str | None = None
    real_name: str | None = None
    is_bot: bool | None = None
    is_admin: bool | None = None
    deleted: bool | None = None
    tz: str | None = None
    profile: Profile | None = None


class UserList(SlackModel):
    """users.list result."""

    members: list[User] = []
    response_metadata: ResponseMetadata | None = None
