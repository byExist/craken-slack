"""Register Slack MCP tools.

All tools are registered; what actually works is governed by the token's OAuth
scopes, which ``capabilities.describe`` annotates per tool (a missing scope adds
an "Unavailable" note). There is no config gate — scopes are the gate.
"""

from collections.abc import Callable
from typing import Any

from mcp.server.fastmcp import FastMCP

from slack_mcp import capabilities, tools

mcp = FastMCP(
    "slack",
    instructions=(
        "Slack workspace access: list and read channels and threads, look up "
        "users, search (needs a user-token scope), post/edit/delete messages, "
        "react, read files, join channels, and DM users. A tool whose description "
        'says "Unavailable" is missing the OAuth scope it needs — tell the user '
        "to add that scope and reinstall the plugin."
    ),
)


def _bind(prefix: str, fns: list[Callable[..., Any]]) -> None:
    for fn in fns:
        mcp.tool(name=f"{prefix}_{fn.__name__}", description=capabilities.describe(fn))(
            fn
        )


_bind(
    "slack",
    [
        tools.get_current_user,
        tools.list_channels,
        tools.get_channel,
        tools.get_channel_history,
        tools.get_thread_replies,
        tools.join_channel,
        tools.open_dm,
        tools.get_permalink,
        tools.list_users,
        tools.get_user,
        tools.get_file,
        tools.download_file,
        tools.search_messages,
        tools.post_message,
        tools.update_message,
        tools.delete_message,
        tools.add_reaction,
        tools.remove_reaction,
    ],
)
