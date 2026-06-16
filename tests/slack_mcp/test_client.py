"""Tests for slack.client — request shaping and response parsing.

Each call goes through a MagicMock(spec=WebClient) (the ``slack_api`` fixture),
so these assert the WebClient method + kwargs and that the JSON ``data`` is
parsed into the right typed model.
"""

from unittest.mock import MagicMock

import pytest
from pytest_mock import MockerFixture

from slack_mcp import client
from slack_mcp.schema.auth import AuthTest
from slack_mcp.schema.channel import Channel, ChannelList
from slack_mcp.schema.file import File
from slack_mcp.schema.message import MessageList, Permalink, PostedMessage
from slack_mcp.schema.search import SearchResult
from slack_mcp.schema.user import User, UserList
from slack_mcp.schema.usergroup import UsergroupList
from support import response


# --- Read ---


def test_get_current_user_calls_auth_test(slack_api: MagicMock):
    slack_api.auth_test.return_value = response(
        {"ok": True, "user": "alice", "user_id": "U1"}
    )

    result = client.get_current_user()

    slack_api.auth_test.assert_called_once_with()
    assert isinstance(result, AuthTest)
    assert result.user_id == "U1"


def test_granted_scopes_parses_oauth_header(slack_api: MagicMock):
    slack_api.auth_test.return_value = response(
        {"ok": True}, headers={"X-OAuth-Scopes": "channels:read, chat:write"}
    )

    result = client.granted_scopes()

    slack_api.auth_test.assert_called_once_with()
    assert result == frozenset({"channels:read", "chat:write"})


def test_granted_scopes_none_when_header_absent(slack_api: MagicMock):
    slack_api.auth_test.return_value = response({"ok": True})  # no headers

    assert client.granted_scopes() is None


def test_list_channels_passes_params(slack_api: MagicMock):
    slack_api.conversations_list.return_value = response(
        {"channels": [{"id": "C1", "name": "general"}]}
    )

    result = client.list_channels(types="public_channel", limit=50, cursor="cur")

    slack_api.conversations_list.assert_called_once_with(
        types="public_channel", limit=50, cursor="cur"
    )
    assert isinstance(result, ChannelList)
    assert result.channels[0].id == "C1"


def test_get_channel_extracts_channel(slack_api: MagicMock):
    slack_api.conversations_info.return_value = response(
        {"channel": {"id": "C1", "name": "general"}}
    )

    result = client.get_channel("C1")

    slack_api.conversations_info.assert_called_once_with(channel="C1")
    assert isinstance(result, Channel)
    assert result.name == "general"


def test_get_channel_history_passes_params(slack_api: MagicMock):
    slack_api.conversations_history.return_value = response(
        {"messages": [{"ts": "1.1", "text": "hi"}], "has_more": False}
    )

    result = client.get_channel_history("C1", limit=10, cursor="cur")

    slack_api.conversations_history.assert_called_once_with(
        channel="C1", limit=10, cursor="cur"
    )
    assert isinstance(result, MessageList)
    assert result.messages[0].text == "hi"


def test_get_thread_replies_passes_ts(slack_api: MagicMock):
    slack_api.conversations_replies.return_value = response({"messages": []})

    result = client.get_thread_replies("C1", "1.1", limit=10, cursor=None)

    slack_api.conversations_replies.assert_called_once_with(
        channel="C1", ts="1.1", limit=10, cursor=None
    )
    assert isinstance(result, MessageList)


def test_list_users_passes_params(slack_api: MagicMock):
    slack_api.users_list.return_value = response({"members": [{"id": "U1"}]})

    result = client.list_users(limit=5, cursor=None)

    slack_api.users_list.assert_called_once_with(limit=5, cursor=None)
    assert isinstance(result, UserList)
    assert result.members[0].id == "U1"


def test_get_user_extracts_user(slack_api: MagicMock):
    slack_api.users_info.return_value = response(
        {"user": {"id": "U1", "real_name": "Alice"}}
    )

    result = client.get_user("U1")

    slack_api.users_info.assert_called_once_with(user="U1")
    assert isinstance(result, User)
    assert result.real_name == "Alice"


def test_list_usergroups_calls_usergroups_list(slack_api: MagicMock):
    slack_api.usergroups_list.return_value = response(
        {"ok": True, "usergroups": [{"id": "S1", "handle": "devs"}]}
    )

    result = client.list_usergroups()

    slack_api.usergroups_list.assert_called_once_with()
    assert isinstance(result, UsergroupList)
    assert result.usergroups[0].handle == "devs"


def test_search_messages_defaults_first_call_to_cursor_star(slack_api: MagicMock):
    slack_api.search_messages.return_value = response(
        {
            "query": "hi",
            "messages": {"total": 1, "matches": [{"text": "hi"}]},
            "response_metadata": {"next_cursor": "CUR"},
        }
    )

    result = client.search_messages("hi", count=20, cursor=None)

    # No cursor -> first call uses "*" (cursor mode); next_cursor is surfaced.
    slack_api.search_messages.assert_called_once_with(query="hi", count=20, cursor="*")
    assert isinstance(result, SearchResult)
    assert result.messages is not None
    assert result.messages.matches[0].text == "hi"
    assert result.response_metadata is not None
    assert result.response_metadata.next_cursor == "CUR"


def test_search_messages_passes_explicit_cursor(slack_api: MagicMock):
    slack_api.search_messages.return_value = response({"query": "hi", "messages": {}})

    client.search_messages("hi", count=20, cursor="CUR")

    slack_api.search_messages.assert_called_once_with(
        query="hi", count=20, cursor="CUR"
    )


def test_get_permalink_passes_params(slack_api: MagicMock):
    slack_api.chat_getPermalink.return_value = response(
        {"ok": True, "channel": "C1", "permalink": "https://x/archives/C1/p1"}
    )

    result = client.get_permalink("C1", "1.2")

    slack_api.chat_getPermalink.assert_called_once_with(channel="C1", message_ts="1.2")
    assert isinstance(result, Permalink)
    assert result.permalink == "https://x/archives/C1/p1"


def test_open_dm_extracts_channel(slack_api: MagicMock):
    slack_api.conversations_open.return_value = response(
        {"ok": True, "channel": {"id": "D1"}}
    )

    result = client.open_dm("U1,U2")

    slack_api.conversations_open.assert_called_once_with(users="U1,U2")
    assert isinstance(result, Channel)
    assert result.id == "D1"


def test_join_channel_extracts_channel(slack_api: MagicMock):
    slack_api.conversations_join.return_value = response(
        {"ok": True, "channel": {"id": "C1", "name": "general"}}
    )

    result = client.join_channel("C1")

    slack_api.conversations_join.assert_called_once_with(channel="C1")
    assert isinstance(result, Channel)
    assert result.name == "general"


def test_get_file_extracts_file(slack_api: MagicMock):
    slack_api.files_info.return_value = response(
        {"ok": True, "file": {"id": "F1", "name": "report.pdf"}}
    )

    result = client.get_file("F1")

    slack_api.files_info.assert_called_once_with(file="F1")
    assert isinstance(result, File)
    assert result.name == "report.pdf"


def test_download_file_fetches_with_bearer_token(
    slack_api: MagicMock, mocker: MockerFixture
):
    slack_api.files_info.return_value = response(
        {
            "ok": True,
            "file": {
                "id": "F1",
                "name": "img.png",
                "url_private_download": "https://files.slack.com/img.png",
            },
        }
    )
    fake_resp = MagicMock()
    fake_resp.__enter__ = lambda s: s
    fake_resp.__exit__ = MagicMock(return_value=False)
    fake_resp.read.return_value = b"\x89PNG"
    fake_resp.headers.get.return_value = "image/png"
    mock_urlopen = mocker.patch("slack_mcp.client.urlopen", return_value=fake_resp)

    data, content_type = client.download_file("F1")

    assert data == b"\x89PNG"
    assert content_type == "image/png"
    req = mock_urlopen.call_args[0][0]
    assert req.get_header("Authorization") == "Bearer xoxb-test"


def test_download_file_raises_when_no_url(slack_api: MagicMock):
    slack_api.files_info.return_value = response(
        {"ok": True, "file": {"id": "F1", "name": "report.pdf"}}
    )

    with pytest.raises(ValueError, match="F1"):
        client.download_file("F1")


# --- Write ---


def test_post_message_passes_text_and_thread(slack_api: MagicMock):
    slack_api.chat_postMessage.return_value = response(
        {"ok": True, "channel": "C1", "ts": "1.2"}
    )

    result = client.post_message("C1", "hello", thread_ts="1.1")

    slack_api.chat_postMessage.assert_called_once_with(
        channel="C1", markdown_text="hello", thread_ts="1.1"
    )
    assert isinstance(result, PostedMessage)
    assert result.ts == "1.2"


def test_update_message_passes_ts_and_text(slack_api: MagicMock):
    slack_api.chat_update.return_value = response(
        {"ok": True, "channel": "C1", "ts": "1.2"}
    )

    result = client.update_message("C1", "1.2", "edited")

    slack_api.chat_update.assert_called_once_with(
        channel="C1", ts="1.2", markdown_text="edited"
    )
    assert isinstance(result, PostedMessage)


def test_delete_message_calls_chat_delete(slack_api: MagicMock):
    slack_api.chat_delete.return_value = response({"ok": True})

    assert client.delete_message("C1", "1.2") is None
    slack_api.chat_delete.assert_called_once_with(channel="C1", ts="1.2")


def test_add_reaction_passes_timestamp_and_name(slack_api: MagicMock):
    slack_api.reactions_add.return_value = response({"ok": True})

    assert client.add_reaction("C1", "1.2", "thumbsup") is None
    slack_api.reactions_add.assert_called_once_with(
        channel="C1", timestamp="1.2", name="thumbsup"
    )


def test_remove_reaction_passes_timestamp_and_name(slack_api: MagicMock):
    slack_api.reactions_remove.return_value = response({"ok": True})

    assert client.remove_reaction("C1", "1.2", "thumbsup") is None
    slack_api.reactions_remove.assert_called_once_with(
        channel="C1", timestamp="1.2", name="thumbsup"
    )
