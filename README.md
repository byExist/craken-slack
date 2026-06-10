<h1 align="center">Slack</h1>

<p align="center">
  <a href="https://github.com/byExist/craken-slack/actions/workflows/ci.yml"><img src="https://github.com/byExist/craken-slack/actions/workflows/ci.yml/badge.svg" alt="CI"></a>
  <a href="https://github.com/byExist/craken"><img src="https://img.shields.io/badge/Claude_Code-plugin-da7756" alt="Claude Code plugin"></a>
  <img src="https://img.shields.io/badge/python-3.13+-3776AB?logo=python&logoColor=white" alt="Python 3.13+">
</p>

<p align="center">
  Slack in Claude — channels, messages, threads, users, and search over the official SDK.
</p>

<p align="center">
  <a href="README.ko.md">한국어</a>
</p>

---

## Why slack?

The Slack Web API is a broad surface — listing channels, reading history and threads, looking up users, searching, and posting. This plugin wraps the official [`slack_sdk`](https://github.com/slackapi/python-slack-sdk) instead of reinventing transport, so rate limiting, cursor pagination, and the `{"ok": false}` error envelope are handled for you, and results come back as compact typed models.

**What it can do is governed by your token's OAuth scopes**, which Slack enforces. Grant only read scopes and the assistant can browse and search but never post; add write scopes to let it post, react, and manage. Any tool whose scope the token lacks is marked *Unavailable* in its description, so the assistant won't attempt a call that would fail.

## Installation

slack runs its MCP server through [uv](https://docs.astral.sh/uv/), so uv must be on your `PATH`:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh   # macOS / Linux — see the uv docs for Windows
```

```bash
/plugin marketplace add byExist/craken
/plugin install slack@craken
```

**Installed disabled** — it connects to your workspace, so you opt in by enabling it (`/plugin` menu, or `claude plugin enable slack`), which prompts for the settings below. The token is stored in your OS keychain, not `settings.json`; reconfigure anytime with `/plugin config slack`.

| Setting | Description |
| --- | --- |
| Slack OAuth token | Bot token (`xoxb-…`) or user token (`xoxp-…`). Create a Slack app at [api.slack.com/apps](https://api.slack.com/apps), add the scopes you want (see below), install it to your workspace, and copy the OAuth token. |

> **Scopes are the permission gate.** The assistant can do exactly what the token's scopes allow — there is no separate write toggle. A tool whose scope is missing is flagged *Unavailable* in its description (and the call would return an actionable `missing_scope` error). Typical sets:
>
> - **Read & search** — `channels:read` · `channels:history` · `users:read` · `files:read` · `search:read` _(add `groups:*` / `im:*` / `mpim:*` for private channels and DMs)_
> - **Write & act** — `chat:write` · `reactions:write` · `channels:join` · `im:write`
>
> **Search needs a user token** (`xoxp-`): `search:read` is a user-token scope, so bot tokens can't call `search.messages`.

## Tools

All tools are namespaced `slack_*` (e.g. `slack_post_message`). Channel and user arguments take a **name or an ID** — `#general` / `@alice` resolve to IDs via `list_channels` / `list_users` (cached in memory for the session).

| Read | Write & act |
| --- | --- |
| `get_current_user` — identity (auth.test) | `post_message` — post, or reply in a thread |
| `list_channels` · `get_channel` | `update_message` · `delete_message` |
| `get_channel_history` · `get_thread_replies` | `add_reaction` · `remove_reaction` |
| `list_users` · `get_user` | `join_channel` — join a public channel to read it |
| `get_file` · `get_permalink` | `open_dm` — open a DM, then post to the channel |
| `search_messages` — user token only | |

## Development

```bash
uv sync
uv run pytest
uv run pyright
```
