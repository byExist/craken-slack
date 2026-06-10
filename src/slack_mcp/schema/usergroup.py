"""Usergroup (subteam) schemas."""

from slack_mcp.schema.base import SlackModel


class Usergroup(SlackModel):
    """A Slack user group (subteam).

    Slack API: a ``usergroups[]`` item from usergroups.list. ``handle`` is the
    ``@mention`` handle; ``id`` is the ``S…`` subteam id used in ``<!subteam^S…>``.
    """

    id: str | None = None
    team_id: str | None = None
    handle: str | None = None
    name: str | None = None
    description: str | None = None
    is_external: bool | None = None
    date_delete: int | None = None  # 0 = active, >0 = disabled


class UsergroupList(SlackModel):
    """usergroups.list result."""

    ok: bool | None = None
    usergroups: list[Usergroup] = []
