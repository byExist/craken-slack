"""auth.test schema."""

from slack_mcp.schema.base import SlackModel


class AuthTest(SlackModel):
    """auth.test result — the authenticated identity and workspace."""

    ok: bool | None = None
    url: str | None = None
    team: str | None = None
    user: str | None = None
    team_id: str | None = None
    user_id: str | None = None
    bot_id: str | None = None
