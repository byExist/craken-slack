# pyright: reportUnknownMemberType=false, reportUnknownArgumentType=false
# Scoped: slack_sdk's WebClient methods take **kwargs: Unknown and SlackResponse.data
# is loosely typed, so these two reports fire only on that third-party surface. The
# rest of the package stays under full strict.
"""Slack Web API client.

Lazy-singleton ``slack_sdk.WebClient`` with module-level functions that return
typed Pydantic models. The client is built on first use so the MCP server can
start even before the token is configured. Every call goes through
``errors.call`` so a ``{"ok": false}`` envelope becomes an actionable error.

Required environment variable
-----------------------------
SLACK_TOKEN - Slack OAuth token (xoxb-… bot or xoxp-… user)
"""

from typing import Any, cast

from slack_sdk import WebClient
from slack_sdk.web import SlackResponse

from slack_mcp.config import get_auth
from slack_mcp.errors import call
from slack_mcp.schema.auth import AuthTest
from slack_mcp.schema.channel import Channel, ChannelList
from slack_mcp.schema.file import File
from slack_mcp.schema.message import MessageList, Permalink, PostedMessage
from slack_mcp.schema.search import SearchResult
from slack_mcp.schema.user import User, UserList
from slack_mcp.schema.usergroup import UsergroupList

# ---------------------------------------------------------------------------
# Lazy singleton
# ---------------------------------------------------------------------------

_client: WebClient | None = None


def _get_client() -> WebClient:
    global _client  # noqa: PLW0603
    if _client is None:
        _client = WebClient(token=get_auth().token.get_secret_value())
    return _client


def _data(resp: SlackResponse) -> dict[str, Any]:
    """Slack Web API responses are JSON objects; expose ``data`` as a dict."""
    return cast(dict[str, Any], resp.data)


# ---------------------------------------------------------------------------
# Read
# ---------------------------------------------------------------------------


def get_current_user() -> AuthTest:
    resp = call(lambda: _get_client().auth_test())
    return AuthTest.model_validate(_data(resp))


def granted_scopes() -> frozenset[str] | None:
    """The token's granted OAuth scopes, from the ``X-OAuth-Scopes`` header on an
    auth.test response. None when the header is absent, so callers treat scopes
    as undeterminable rather than empty."""
    resp = call(lambda: _get_client().auth_test())
    headers = cast(dict[str, str], resp.headers)
    raw = next((v for k, v in headers.items() if k.lower() == "x-oauth-scopes"), None)
    if raw is None:
        return None
    return frozenset(s.strip() for s in raw.split(",") if s.strip())


def list_channels(
    *,
    types: str = "public_channel",
    limit: int = 100,
    cursor: str | None = None,
) -> ChannelList:
    resp = call(
        lambda: _get_client().conversations_list(
            types=types, limit=limit, cursor=cursor
        )
    )
    return ChannelList.model_validate(_data(resp))


def get_channel(channel_id: str) -> Channel:
    resp = call(lambda: _get_client().conversations_info(channel=channel_id))
    return Channel.model_validate(_data(resp)["channel"])


def get_channel_history(
    channel_id: str,
    *,
    limit: int = 100,
    cursor: str | None = None,
) -> MessageList:
    resp = call(
        lambda: _get_client().conversations_history(
            channel=channel_id, limit=limit, cursor=cursor
        )
    )
    return MessageList.model_validate(_data(resp))


def get_thread_replies(
    channel_id: str,
    thread_ts: str,
    *,
    limit: int = 100,
    cursor: str | None = None,
) -> MessageList:
    resp = call(
        lambda: _get_client().conversations_replies(
            channel=channel_id, ts=thread_ts, limit=limit, cursor=cursor
        )
    )
    return MessageList.model_validate(_data(resp))


def list_users(
    *,
    limit: int = 100,
    cursor: str | None = None,
) -> UserList:
    resp = call(lambda: _get_client().users_list(limit=limit, cursor=cursor))
    return UserList.model_validate(_data(resp))


def get_user(user_id: str) -> User:
    resp = call(lambda: _get_client().users_info(user=user_id))
    return User.model_validate(_data(resp)["user"])


def list_usergroups() -> UsergroupList:
    resp = call(lambda: _get_client().usergroups_list())
    return UsergroupList.model_validate(_data(resp))


def search_messages(
    query: str,
    *,
    count: int = 20,
    cursor: str | None = None,
) -> SearchResult:
    # search.messages cursor pagination expects "*" on the first call, then the
    # response's next_cursor; default None -> "*" so the first call is cursor mode
    # (without it Slack falls back to page mode and never returns next_cursor).
    resp = call(
        lambda: _get_client().search_messages(
            query=query, count=count, cursor=cursor or "*"
        )
    )
    return SearchResult.model_validate(_data(resp))


def get_permalink(channel: str, message_ts: str) -> Permalink:
    resp = call(
        lambda: _get_client().chat_getPermalink(channel=channel, message_ts=message_ts)
    )
    return Permalink.model_validate(_data(resp))


def open_dm(users: str) -> Channel:
    resp = call(lambda: _get_client().conversations_open(users=users))
    return Channel.model_validate(_data(resp)["channel"])


def join_channel(channel_id: str) -> Channel:
    resp = call(lambda: _get_client().conversations_join(channel=channel_id))
    return Channel.model_validate(_data(resp)["channel"])


def get_file(file_id: str) -> File:
    resp = call(lambda: _get_client().files_info(file=file_id))
    return File.model_validate(_data(resp)["file"])


# ---------------------------------------------------------------------------
# Write
# ---------------------------------------------------------------------------


def post_message(
    channel: str,
    text: str,
    *,
    thread_ts: str | None = None,
) -> PostedMessage:
    # `markdown_text` renders standard Markdown (Slack converts it); the mrkdwn
    # `text` field would mis-render an LLM's Markdown. Mentions still need encoded
    # tokens (<@U…>), resolved from names by callers.
    resp = call(
        lambda: _get_client().chat_postMessage(
            channel=channel, markdown_text=text, thread_ts=thread_ts
        )
    )
    return PostedMessage.model_validate(_data(resp))


def update_message(channel: str, ts: str, text: str) -> PostedMessage:
    resp = call(
        lambda: _get_client().chat_update(channel=channel, ts=ts, markdown_text=text)
    )
    return PostedMessage.model_validate(_data(resp))


def delete_message(channel: str, ts: str) -> None:
    call(lambda: _get_client().chat_delete(channel=channel, ts=ts))


def add_reaction(channel: str, timestamp: str, name: str) -> None:
    call(
        lambda: _get_client().reactions_add(
            channel=channel, timestamp=timestamp, name=name
        )
    )


def remove_reaction(channel: str, timestamp: str, name: str) -> None:
    call(
        lambda: _get_client().reactions_remove(
            channel=channel, timestamp=timestamp, name=name
        )
    )
