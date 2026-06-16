"""Tests for slack.server — tool registration and scope annotation.

server.py registers all tools at import time; ``capabilities.describe`` annotates
any whose required OAuth scope is absent. The module is reloaded with a controlled
scope set (``capabilities._granted`` patched) so the reload never hits the network.
"""

import importlib

from pytest_mock import MockerFixture

ALL = [
    "slack_get_current_user",
    "slack_list_channels",
    "slack_get_channel",
    "slack_get_channel_history",
    "slack_get_thread_replies",
    "slack_join_channel",
    "slack_open_dm",
    "slack_get_permalink",
    "slack_list_users",
    "slack_get_user",
    "slack_get_file",
    "slack_download_file",
    "slack_search_messages",
    "slack_post_message",
    "slack_update_message",
    "slack_delete_message",
    "slack_add_reaction",
    "slack_remove_reaction",
]


def _tool_map(
    mocker: MockerFixture, *, scopes: frozenset[str] | None = None
) -> dict[str, str]:
    """Reload server.py with a controlled scope probe; return {name: description}."""
    import slack_mcp.server as server_module
    from slack_mcp import capabilities

    mocker.patch.object(capabilities, "_granted", lambda: scopes)
    server_module = importlib.reload(server_module)
    return {
        tool.name: tool.description or ""
        for tool in server_module.mcp._tool_manager.list_tools()
    }


def test_all_tools_registered(mocker: MockerFixture):
    tools = _tool_map(mocker)

    for name in ALL:
        assert name in tools


def test_all_tools_namespaced_and_documented(mocker: MockerFixture):
    tools = _tool_map(mocker)

    assert tools  # sanity: something registered
    assert all(name.startswith("slack_") for name in tools)
    assert all(desc for desc in tools.values())  # every tool keeps a description


def test_missing_scope_annotates_matching_tool(mocker: MockerFixture):
    # Token holds only a read scope -> chat:write tools are flagged Unavailable.
    tools = _tool_map(mocker, scopes=frozenset({"channels:read"}))

    assert "Unavailable:" in tools["slack_post_message"]
    assert "chat:write" in tools["slack_post_message"]
    assert "Unavailable:" not in tools["slack_list_channels"]


def test_present_scope_leaves_tool_plain(mocker: MockerFixture):
    tools = _tool_map(mocker, scopes=frozenset({"chat:write"}))

    assert "Unavailable:" not in tools["slack_post_message"]


def test_unknown_scopes_annotate_nothing(mocker: MockerFixture):
    tools = _tool_map(mocker, scopes=None)  # probe failed

    assert all("Unavailable:" not in desc for desc in tools.values())
