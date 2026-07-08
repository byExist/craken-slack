"""Tests for slack.tools — the MCP tool layer (thin delegation to client)."""

from unittest.mock import call

from pytest_mock import MockerFixture

from slack_mcp import client, files, tools


def test_get_current_user_delegates(mocker: MockerFixture):
    sentinel = object()
    fn = mocker.patch.object(client, "get_current_user", return_value=sentinel)

    assert tools.get_current_user() is sentinel
    assert fn.call_args == call()


def test_list_channels_delegates(mocker: MockerFixture):
    sentinel = object()
    fn = mocker.patch.object(client, "list_channels", return_value=sentinel)

    assert tools.list_channels(types="im", limit=5, cursor="c") is sentinel
    assert fn.call_args == call(types="im", limit=5, cursor="c")


def test_get_channel_delegates(mocker: MockerFixture):
    sentinel = object()
    fn = mocker.patch.object(client, "get_channel", return_value=sentinel)

    assert tools.get_channel("C1") is sentinel
    assert fn.call_args == call("C1")


def test_get_channel_history_delegates(mocker: MockerFixture):
    sentinel = object()
    fn = mocker.patch.object(client, "get_channel_history", return_value=sentinel)

    assert tools.get_channel_history("C1", limit=5, cursor="c") is sentinel
    assert fn.call_args == call("C1", limit=5, cursor="c")


def test_get_thread_replies_delegates(mocker: MockerFixture):
    sentinel = object()
    fn = mocker.patch.object(client, "get_thread_replies", return_value=sentinel)

    assert tools.get_thread_replies("C1", "1.1", limit=5, cursor="c") is sentinel
    assert fn.call_args == call("C1", "1.1", limit=5, cursor="c", oldest=None)


def test_list_users_delegates(mocker: MockerFixture):
    sentinel = object()
    fn = mocker.patch.object(client, "list_users", return_value=sentinel)

    assert tools.list_users(limit=5, cursor="c") is sentinel
    assert fn.call_args == call(limit=5, cursor="c")


def test_get_user_delegates(mocker: MockerFixture):
    sentinel = object()
    fn = mocker.patch.object(client, "get_user", return_value=sentinel)

    assert tools.get_user("U1") is sentinel
    assert fn.call_args == call("U1")


def test_search_messages_maps_limit_to_count(mocker: MockerFixture):
    sentinel = object()
    fn = mocker.patch.object(client, "search_messages", return_value=sentinel)

    assert tools.search_messages("hi", limit=10, cursor="c") is sentinel
    assert fn.call_args == call("hi", count=10, cursor="c")


def test_join_channel_delegates(mocker: MockerFixture):
    sentinel = object()
    fn = mocker.patch.object(client, "join_channel", return_value=sentinel)

    assert tools.join_channel("C1") is sentinel
    assert fn.call_args == call("C1")


def test_open_dm_resolves_and_delegates(mocker: MockerFixture):
    sentinel = object()
    fn = mocker.patch.object(client, "open_dm", return_value=sentinel)

    assert tools.open_dm("U1, U2") is sentinel  # spaces trimmed, IDs pass through
    assert fn.call_args == call("U1,U2")


def test_get_permalink_delegates(mocker: MockerFixture):
    sentinel = object()
    fn = mocker.patch.object(client, "get_permalink", return_value=sentinel)

    assert tools.get_permalink("C1", "1.2") is sentinel
    assert fn.call_args == call("C1", "1.2")


def test_get_file_delegates(mocker: MockerFixture):
    sentinel = object()
    fn = mocker.patch.object(client, "get_file", return_value=sentinel)

    assert tools.get_file("F1") is sentinel
    assert fn.call_args == call("F1")


def test_download_file_delegates(mocker: MockerFixture):
    mocker.patch.object(client, "download_file", return_value=(b"data", "image/png"))
    sentinel = object()
    mocker.patch.object(files, "write_temp", return_value=sentinel)

    assert tools.download_file("F1") is sentinel


def test_post_message_delegates(mocker: MockerFixture):
    sentinel = object()
    fn = mocker.patch.object(client, "post_message", return_value=sentinel)

    assert tools.post_message("C1", "hi", thread_ts="1.1") is sentinel
    assert fn.call_args == call("C1", "hi", thread_ts="1.1")


def test_update_message_delegates(mocker: MockerFixture):
    sentinel = object()
    fn = mocker.patch.object(client, "update_message", return_value=sentinel)

    assert tools.update_message("C1", "1.2", "edited") is sentinel
    assert fn.call_args == call("C1", "1.2", "edited")


def test_delete_message_delegates(mocker: MockerFixture):
    fn = mocker.patch.object(client, "delete_message")

    assert tools.delete_message("C1", "1.2") == "ok"
    assert fn.call_args == call("C1", "1.2")


def test_add_reaction_delegates(mocker: MockerFixture):
    fn = mocker.patch.object(client, "add_reaction")

    assert tools.add_reaction("C1", "1.2", "tada") == "ok"
    assert fn.call_args == call("C1", "1.2", "tada")


def test_remove_reaction_delegates(mocker: MockerFixture):
    fn = mocker.patch.object(client, "remove_reaction")

    assert tools.remove_reaction("C1", "1.2", "tada") == "ok"
    assert fn.call_args == call("C1", "1.2", "tada")
