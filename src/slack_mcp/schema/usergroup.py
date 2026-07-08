"""Usergroup (subteam) schemas."""

from slack_mcp.schema.base import SlackModel


class Usergroup(SlackModel):
    """A Slack user group (subteam).

    Slack API: a ``usergroups[]`` item from usergroups.list. ``handle`` is the
    ``@mention`` handle; ``id`` is the ``S…`` subteam id used in ``<!subteam^S…>``.
    """

    id: str
    team_id: str
    handle: str
    name: str
    description: str
    is_external: bool
    date_delete: int  # 0 = active, >0 = disabled


class UsergroupList(SlackModel):
    """usergroups.list result."""

    usergroups: list[Usergroup] = []
