"""auth.test schema."""

from slack_mcp.schema.base import SlackModel


class AuthTest(SlackModel):
    """auth.test result — the authenticated identity and workspace."""

    url: str
    team: str
    user: str
    team_id: str
    user_id: str
    bot_id: str | None = None
