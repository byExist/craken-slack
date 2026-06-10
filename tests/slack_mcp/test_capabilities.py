"""Tests for slack_mcp.capabilities — scope-driven tool-description hints.

``client.granted_scopes`` is patched so detection never hits the network: a scope
set (or None) drives whether a tool is annotated. The probe cache is cleared
between tests by the autouse fixture (``capabilities.reset`` in conftest).
"""

from pytest_mock import MockerFixture

from slack_mcp import capabilities, client, tools


def _patch_scopes(mocker: MockerFixture, scopes: frozenset[str] | None) -> None:
    capabilities.reset()
    mocker.patch.object(client, "granted_scopes", return_value=scopes)


# --- _granted (cached probe) ---


def test_granted_returns_scopes(mocker: MockerFixture):
    _patch_scopes(mocker, frozenset({"chat:write"}))

    assert capabilities._granted() == frozenset({"chat:write"})


def test_granted_swallows_probe_failure(mocker: MockerFixture):
    capabilities.reset()
    mocker.patch.object(client, "granted_scopes", side_effect=RuntimeError("boom"))

    assert capabilities._granted() is None


def test_granted_is_cached(mocker: MockerFixture):
    capabilities.reset()
    fn = mocker.patch.object(client, "granted_scopes", return_value=frozenset())

    capabilities._granted()
    capabilities._granted()

    fn.assert_called_once()  # probed once, then served from cache


# --- describe ---


def test_describe_annotates_tool_missing_scope(mocker: MockerFixture):
    _patch_scopes(mocker, frozenset({"channels:read"}))  # lacks chat:write

    doc = capabilities.describe(tools.post_message)

    assert "Unavailable:" in doc
    assert "chat:write" in doc
    # Original docstring is preserved ahead of the note.
    assert doc.startswith((tools.post_message.__doc__ or "").rstrip())


def test_describe_leaves_tool_plain_when_scope_present(mocker: MockerFixture):
    _patch_scopes(mocker, frozenset({"chat:write"}))

    doc = capabilities.describe(tools.post_message)

    assert "Unavailable:" not in doc
    assert doc == (tools.post_message.__doc__ or "").rstrip()


def test_describe_handles_any_of_scopes(mocker: MockerFixture):
    # get_channel_history accepts ANY *:history scope; one is enough.
    _patch_scopes(mocker, frozenset({"groups:history"}))

    doc = capabilities.describe(tools.get_channel_history)

    assert "Unavailable:" not in doc


def test_describe_annotates_search_without_search_scope(mocker: MockerFixture):
    # The old token-type special case, now subsumed by scope detection.
    _patch_scopes(mocker, frozenset({"channels:read"}))

    doc = capabilities.describe(tools.search_messages)

    assert "Unavailable:" in doc
    assert "search:read" in doc


def test_describe_skips_when_scopes_unknown(mocker: MockerFixture):
    _patch_scopes(mocker, None)  # probe failed -> never annotate

    doc = capabilities.describe(tools.post_message)

    assert "Unavailable:" not in doc


def test_describe_ignores_unmapped_tool(mocker: MockerFixture):
    # get_current_user (auth.test) needs no scope -> never annotated.
    _patch_scopes(mocker, frozenset())

    doc = capabilities.describe(tools.get_current_user)

    assert "Unavailable:" not in doc


def test_describe_handles_missing_docstring(mocker: MockerFixture):
    _patch_scopes(mocker, frozenset({"channels:read"}))

    def post_message():  # name maps to chat:write; no docstring
        pass

    doc = capabilities.describe(post_message)

    assert "Unavailable:" in doc
