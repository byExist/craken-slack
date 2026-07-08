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
    """A message author's inlined profile (``Message.user_profile``).

    Slack API: ``objs_user_profile_short``. Distinct from the fuller ``Profile``
    (users.info); only the naming subset is kept.
    """

    name: str | None = None
    real_name: str | None = None
    display_name: str | None = None


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
