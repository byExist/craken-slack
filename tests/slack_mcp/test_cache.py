"""Tests for slack_mcp.cache — name → ID resolution.

``client.list_channels`` / ``list_users`` are patched directly (no network), so
these exercise the resolver's own logic: ID pass-through, lazy build, warm-hit,
refresh-on-miss, pagination, skipping incomplete entries, and not-found errors.
The cache is reset between tests by the autouse ``isolate_env`` fixture.
"""

import pytest
from pytest_mock import MockerFixture

from slack_mcp import cache, client
from slack_mcp.schema.channel import ChannelList, ResponseMetadata
from slack_mcp.schema.message import Message, MessageList
from slack_mcp.schema.user import UserList
from slack_mcp.schema.usergroup import UsergroupList
from support import channel_model, message, profile, user_model, usergroup_model


# --- Channels ---


def test_resolve_channel_passes_through_id(mocker: MockerFixture):
    spy = mocker.patch.object(client, "list_channels")

    assert cache.resolve_channel("C0123ABCD") == "C0123ABCD"
    spy.assert_not_called()  # an ID never triggers a listing


def test_resolve_channel_by_name_then_warm_hit(mocker: MockerFixture):
    fetch = mocker.patch.object(
        client,
        "list_channels",
        return_value=ChannelList(channels=[channel_model(name="general")]),
    )

    assert cache.resolve_channel("#general") == "C1"  # cold build
    assert cache.resolve_channel("general") == "C1"  # warm hit, no '#'
    fetch.assert_called_once()  # second lookup served from cache


def test_resolve_channel_not_found_raises(mocker: MockerFixture):
    mocker.patch.object(
        client,
        "list_channels",
        return_value=ChannelList(channels=[channel_model(name="general")]),
    )

    with pytest.raises(ValueError, match="nope"):
        cache.resolve_channel("#nope")


def test_resolve_channel_refreshes_on_miss(mocker: MockerFixture):
    mocker.patch.object(
        client,
        "list_channels",
        side_effect=[
            ChannelList(channels=[channel_model(name="general")]),
            ChannelList(
                channels=[
                    channel_model(name="general"),
                    channel_model(id="C2", name="new"),
                ]
            ),
        ],
    )

    assert cache.resolve_channel("#general") == "C1"  # cold build (1st page set)
    assert cache.resolve_channel("#new") == "C2"  # warm miss → refresh finds it


def test_resolve_channel_paginates(mocker: MockerFixture):
    mocker.patch.object(
        client,
        "list_channels",
        side_effect=[
            ChannelList(
                channels=[channel_model(name="general")],
                response_metadata=ResponseMetadata(next_cursor="cur"),
            ),
            ChannelList(channels=[channel_model(id="C2", name="random")]),
        ],
    )

    assert cache.resolve_channel("#random") == "C2"  # found on the second page


def test_resolve_channel_skips_incomplete_entries(mocker: MockerFixture):
    mocker.patch.object(
        client,
        "list_channels",
        return_value=ChannelList(
            channels=[
                channel_model(name="general"),
                channel_model(id="C2", name=""),  # empty name → skipped
                channel_model(id="", name="ghost"),  # empty id → skipped
            ]
        ),
    )

    assert cache.resolve_channel("#general") == "C1"
    with pytest.raises(ValueError, match="ghost"):
        cache.resolve_channel("#ghost")


# --- Users ---


def test_resolve_user_passes_through_id(mocker: MockerFixture):
    spy = mocker.patch.object(client, "list_users")

    assert cache.resolve_user("U0123ABCD") == "U0123ABCD"
    spy.assert_not_called()


def test_resolve_user_by_handle_then_warm_hit(mocker: MockerFixture):
    fetch = mocker.patch.object(
        client,
        "list_users",
        return_value=UserList(members=[user_model(name="alice")]),
    )

    assert cache.resolve_user("@alice") == "U1"  # cold build
    assert cache.resolve_user("alice") == "U1"  # warm hit
    fetch.assert_called_once()


def test_resolve_user_not_found_raises(mocker: MockerFixture):
    mocker.patch.object(
        client,
        "list_users",
        return_value=UserList(members=[user_model(name="alice")]),
    )

    with pytest.raises(ValueError, match="bob"):
        cache.resolve_user("@bob")


def test_resolve_user_refreshes_on_miss(mocker: MockerFixture):
    mocker.patch.object(
        client,
        "list_users",
        side_effect=[
            UserList(members=[user_model(name="alice")]),
            UserList(
                members=[
                    user_model(name="alice"),
                    user_model(id="U2", name="bob"),
                ]
            ),
        ],
    )

    assert cache.resolve_user("@alice") == "U1"  # cold
    assert cache.resolve_user("@bob") == "U2"  # warm miss → refresh finds it


def test_resolve_user_paginates_and_skips_incomplete(mocker: MockerFixture):
    mocker.patch.object(
        client,
        "list_users",
        side_effect=[
            UserList(
                members=[
                    user_model(name="alice"),
                    user_model(id="U2", name=""),  # empty name → skipped
                ],
                response_metadata=ResponseMetadata(next_cursor="cur"),
            ),
            UserList(members=[user_model(id="U3", name="bob")]),
        ],
    )

    assert cache.resolve_user("@bob") == "U3"  # found on the second page


# --- Mention substitution ---


def test_substitute_user_mention(mocker: MockerFixture):
    mocker.patch.object(
        client,
        "list_users",
        return_value=UserList(members=[user_model(name="alice")]),
    )
    mocker.patch.object(
        client, "list_usergroups", return_value=UsergroupList(usergroups=[])
    )

    assert cache.substitute_mentions("hi @alice!") == "hi <@U1>!"


def test_substitute_usergroup_mention_skips_incomplete(mocker: MockerFixture):
    mocker.patch.object(client, "list_users", return_value=UserList(members=[]))
    mocker.patch.object(
        client,
        "list_usergroups",
        return_value=UsergroupList(
            usergroups=[
                usergroup_model(),
                usergroup_model(id="S2", handle=""),  # empty handle → skipped
            ]
        ),
    )

    assert cache.substitute_mentions("@devs ship it") == "<!subteam^S1> ship it"


def test_substitute_special_mentions(mocker: MockerFixture):
    mocker.patch.object(client, "list_users", return_value=UserList(members=[]))
    mocker.patch.object(
        client, "list_usergroups", return_value=UsergroupList(usergroups=[])
    )

    assert (
        cache.substitute_mentions("@here @channel @everyone")
        == "<!here> <!channel> <!everyone>"
    )


def test_substitute_unknown_handle_left_literal(mocker: MockerFixture):
    mocker.patch.object(client, "list_users", return_value=UserList(members=[]))
    mocker.patch.object(
        client, "list_usergroups", return_value=UsergroupList(usergroups=[])
    )

    assert cache.substitute_mentions("ping @nobody") == "ping @nobody"


def test_substitute_channel_reference(mocker: MockerFixture):
    mocker.patch.object(
        client,
        "list_channels",
        return_value=ChannelList(channels=[channel_model(name="general")]),
    )

    assert cache.substitute_mentions("see #general please") == "see <#C1> please"


def test_substitute_unknown_channel_left_literal(mocker: MockerFixture):
    mocker.patch.object(client, "list_channels", return_value=ChannelList(channels=[]))

    assert cache.substitute_mentions("ticket #42 done") == "ticket #42 done"


def test_substitute_leaves_protected_regions():
    # Code, links, existing tokens are masked; a header's `#` is not a channel.
    text = "```@alice``` `@bob` [t](http://u) <#C9>\n# Heading"

    assert cache.substitute_mentions(text) == text


def test_substitute_handles_listing_failure(mocker: MockerFixture):
    mocker.patch.object(client, "list_users", side_effect=RuntimeError("boom"))
    mocker.patch.object(
        client, "list_usergroups", return_value=UsergroupList(usergroups=[])
    )

    # user listing failed → @alice can't resolve → left literal, no crash
    assert cache.substitute_mentions("@alice") == "@alice"


# --- id → name reverse resolution / enrichment ---


def test_resolve_user_profile_lazy_then_cached(mocker: MockerFixture):
    fetch = mocker.patch.object(
        client,
        "list_users",
        return_value=UserList(
            members=[
                user_model(
                    name="alice",
                    real_name="Alice Kim",
                    profile=profile(display_name="al"),
                )
            ]
        ),
    )

    p = cache.resolve_user_profile("U1")
    assert p is not None
    assert p.model_dump() == {
        "name": "alice",
        "real_name": "Alice Kim",
        "display_name": "al",
    }
    assert cache.resolve_user_profile("U1") is not None  # warm hit
    fetch.assert_called_once()  # built once, then cached


def test_resolve_user_profile_miss_returns_none(mocker: MockerFixture):
    mocker.patch.object(
        client, "list_users", return_value=UserList(members=[user_model(name="alice")])
    )

    assert cache.resolve_user_profile("U404") is None  # not in workspace → raw id kept


def test_resolve_user_profile_graceful_on_failure(mocker: MockerFixture):
    mocker.patch.object(client, "list_users", side_effect=RuntimeError("boom"))

    assert cache.resolve_user_profile("U1") is None  # listing failed → None, no crash


def test_resolve_user_profile_paginates_and_skips_incomplete(mocker: MockerFixture):
    fetch = mocker.patch.object(
        client,
        "list_users",
        side_effect=[
            UserList(
                members=[
                    user_model(id="", name="ghost"),  # no id → skipped entirely
                    user_model(id="U3", name=""),  # no name → id resolves, not handle
                ],
                response_metadata=ResponseMetadata(next_cursor="cur"),
            ),
            UserList(members=[user_model(id="U2", name="bob", real_name="Bob")]),
        ],
    )

    assert cache.resolve_user_profile("U2") is not None  # found on the 2nd page
    assert cache.resolve_user_profile("U3") is not None  # id kept despite empty name
    # forward map warmed from the same fetch → resolving @bob needs no refetch
    assert cache.resolve_user("@bob") == "U2"
    assert fetch.call_count == 2  # two pages of the one build; no extra fetch


def test_enrich_messages_fills_user_profile(mocker: MockerFixture):
    mocker.patch.object(
        client,
        "list_users",
        return_value=UserList(
            members=[
                user_model(
                    name="alice",
                    real_name="Alice Kim",
                    profile=profile(display_name="al"),
                )
            ]
        ),
    )
    msgs = MessageList(
        messages=[
            Message.model_validate(message(user="U1")),
            Message.model_validate(message()),  # no user → skipped
        ]
    )

    cache.enrich_messages(msgs)

    assert msgs.messages[0].user_profile is not None
    assert msgs.messages[0].user_profile.display_name == "al"
    assert msgs.messages[0].user == "U1"  # raw id kept
    assert msgs.messages[1].user_profile is None  # no user → untouched


def test_enrich_messages_keeps_slack_inlined_profile(mocker: MockerFixture):
    fetch = mocker.patch.object(client, "list_users", return_value=UserList(members=[]))
    msg = Message.model_validate(
        message(
            user="U1",
            user_profile={
                "name": "inlined",
                "real_name": "Inlined",
                "display_name": "inl",
            },
        )
    )

    cache.enrich_messages(MessageList(messages=[msg]))

    assert msg.user_profile is not None
    assert msg.user_profile.display_name == "inl"  # not overwritten
    fetch.assert_not_called()  # already inlined → no resolution, no fetch
