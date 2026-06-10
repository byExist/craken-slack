<h1 align="center">Slack</h1>

<p align="center">
  <a href="https://github.com/byExist/craken-slack/actions/workflows/ci.yml"><img src="https://github.com/byExist/craken-slack/actions/workflows/ci.yml/badge.svg" alt="CI"></a>
  <a href="https://github.com/byExist/craken"><img src="https://img.shields.io/badge/Claude_Code-plugin-da7756" alt="Claude Code plugin"></a>
  <img src="https://img.shields.io/badge/python-3.13+-3776AB?logo=python&logoColor=white" alt="Python 3.13+">
</p>

<p align="center">
  Claude에서 Slack — 채널·메시지·스레드·사용자·검색을 공식 SDK 위에서.
</p>

<p align="center">
  <a href="README.md">English</a>
</p>

---

## 왜 slack인가?

Slack Web API는 표면이 넓습니다 — 채널 목록, 히스토리·스레드 읽기, 사용자 조회, 검색, 메시지 작성. 이 플러그인은 transport를 직접 만들지 않고 공식 [`slack_sdk`](https://github.com/slackapi/python-slack-sdk)를 감쌉니다. 그래서 레이트리밋, 커서 페이지네이션, `{"ok": false}` 에러 엔벨로프가 알아서 처리되고, 결과는 None을 덜어낸 typed 모델로 돌아옵니다.

**무엇을 할 수 있는지는 토큰의 OAuth scope가 결정합니다** — Slack이 직접 강제합니다. 읽기 scope만 부여하면 어시스턴트는 둘러보고 검색만 할 뿐 글은 못 쓰고, 쓰기 scope를 더하면 작성·리액션·관리까지 가능합니다. 토큰에 scope가 없는 도구는 설명에 *Unavailable*로 표시되어, 어시스턴트가 실패할 호출을 시도하지 않습니다.

## 설치

slack은 MCP 서버를 [uv](https://docs.astral.sh/uv/)로 실행하므로 uv가 `PATH`에 있어야 합니다:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh   # macOS / Linux — Windows는 uv 문서 참고
```

```bash
/plugin marketplace add byExist/craken
/plugin install slack@craken
```

**비활성 상태로 설치됩니다** — 워크스페이스에 연결되므로, 활성화(`/plugin` 메뉴 또는 `claude plugin enable slack`)로 직접 opt-in 하면 아래 설정을 묻습니다. 토큰은 `settings.json`이 아니라 OS 키체인에 저장되고, `/plugin config slack`로 언제든 다시 설정할 수 있습니다.

| 설정 | 설명 |
| --- | --- |
| Slack OAuth 토큰 | 봇 토큰(`xoxb-…`) 또는 유저 토큰(`xoxp-…`). [api.slack.com/apps](https://api.slack.com/apps)에서 Slack 앱을 만들고 원하는 scope를 추가(아래 참고)해 워크스페이스에 설치한 뒤 OAuth 토큰을 복사. |

> **scope가 곧 권한 게이트입니다.** 어시스턴트는 토큰의 scope가 허용하는 만큼만 할 수 있고 — 별도 쓰기 토글은 없습니다. scope가 없는 도구는 설명에 *Unavailable*로 표시됩니다(호출하면 actionable한 `missing_scope` 에러). 대표 조합:
>
> - **읽기·검색** — `channels:read` · `channels:history` · `users:read` · `files:read` · `search:read` _(비공개 채널·DM은 `groups:*` / `im:*` / `mpim:*` 추가)_
> - **쓰기·동작** — `chat:write` · `reactions:write` · `channels:join` · `im:write`
>
> **검색은 유저 토큰(`xoxp-`)이 필요**: `search:read`가 유저 토큰 scope라 봇 토큰으로는 `search.messages`를 호출할 수 없습니다.

## 도구

모든 도구는 `slack_*`로 네임스페이스됩니다(예: `slack_post_message`). 채널·유저 인자는 **이름 또는 ID** 둘 다 받습니다 — `#general`·`@alice`는 `list_channels`/`list_users`로 ID를 해석(세션 동안 인메모리 캐시)합니다.

| 읽기 | 쓰기·동작 |
| --- | --- |
| `get_current_user` — 신원(auth.test) | `post_message` — 작성 또는 스레드 답글 |
| `list_channels` · `get_channel` | `update_message` · `delete_message` |
| `get_channel_history` · `get_thread_replies` | `add_reaction` · `remove_reaction` |
| `list_users` · `get_user` | `join_channel` — 공개 채널 가입(읽기용) |
| `get_file` · `get_permalink` | `open_dm` — DM 열기 후 그 채널에 작성 |
| `search_messages` — 유저 토큰 전용 | |

## 개발

```bash
uv sync
uv run pytest
uv run pyright
```
