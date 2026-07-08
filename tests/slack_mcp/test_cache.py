"""Tests for slack_mcp.cache — name → ID resolution.

``client.list_channels`` / ``list_users`` are patched directly (no network), so
these exercise the resolver's own logic: ID pass-through, lazy build, warm-hit,
refresh-on-miss, pagination, skipping incomplete entries, and not-found errors.
The cache is reset between tests by the autouse ``isolate_env`` fixture.
"""

import pytest
from pytest_mock import MockerFixture

from slack_mcp import cache, client
from slack_mcp.schema.channel import Channel, ChannelList, ResponseMetadata
from slack_mcp.schema.user import User, UserList
from slack_mcp.schema.usergroup import Usergroup, UsergroupList
from support import channel, user


# --- Channels ---


def test_resolve_channel_passes_through_id(mocker: MockerFixture):
    spy = mocker.patch.object(client, "list_channels")

    assert cache.resolve_channel("C0123ABCD") == "C0123ABCD"
    spy.assert_not_called()  # an ID never triggers a listing


def test_resolve_channel_by_name_then_warm_hit(mocker: MockerFixture):
    fetch = mocker.patch.object(
        client,
        "list_channels",
        return_value=ChannelList(
            channels=[Channel.model_validate(channel(name="general"))]
        ),
    )

    assert cache.resolve_channel("#general") == "C1"  # cold build
    assert cache.resolve_channel("general") == "C1"  # warm hit, no '#'
    fetch.assert_called_once()  # second lookup served from cache


def test_resolve_channel_not_found_raises(mocker: MockerFixture):
    mocker.patch.object(
        client,
        "list_channels",
        return_value=ChannelList(
            channels=[Channel.model_validate(channel(name="general"))]
        ),
    )

    with pytest.raises(ValueError, match="nope"):
        cache.resolve_channel("#nope")


def test_resolve_channel_refreshes_on_miss(mocker: MockerFixture):
    mocker.patch.object(
        client,
        "list_channels",
        side_effect=[
            ChannelList(channels=[Channel.model_validate(channel(name="general"))]),
            ChannelList(
                channels=[
                    Channel.model_validate(channel(name="general")),
                    Channel.model_validate(channel(id="C2", name="new")),
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
                channels=[Channel.model_validate(channel(name="general"))],
                response_metadata=ResponseMetadata(next_cursor="cur"),
            ),
            ChannelList(
                channels=[Channel.model_validate(channel(id="C2", name="random"))]
            ),
        ],
    )

    assert cache.resolve_channel("#random") == "C2"  # found on the second page


def test_resolve_channel_skips_incomplete_entries(mocker: MockerFixture):
    mocker.patch.object(
        client,
        "list_channels",
        return_value=ChannelList(
            channels=[
                Channel.model_validate(channel(name="general")),
                Channel.model_validate(
                    channel(id="C2", name="")
                ),  # empty name → skipped
                Channel.model_validate(
                    channel(id="", name="ghost")
                ),  # empty id → skipped
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
        return_value=UserList(members=[User.model_validate(user(name="alice"))]),
    )

    assert cache.resolve_user("@alice") == "U1"  # cold build
    assert cache.resolve_user("alice") == "U1"  # warm hit
    fetch.assert_called_once()


def test_resolve_user_not_found_raises(mocker: MockerFixture):
    mocker.patch.object(
        client,
        "list_users",
        return_value=UserList(members=[User.model_validate(user(name="alice"))]),
    )

    with pytest.raises(ValueError, match="bob"):
        cache.resolve_user("@bob")


def test_resolve_user_refreshes_on_miss(mocker: MockerFixture):
    mocker.patch.object(
        client,
        "list_users",
        side_effect=[
            UserList(members=[User.model_validate(user(name="alice"))]),
            UserList(
                members=[
                    User.model_validate(user(name="alice")),
                    User.model_validate(user(id="U2", name="bob")),
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
                    User.model_validate(user(name="alice")),
                    User.model_validate(user(id="U2", name="")),  # empty name → skipped
                ],
                response_metadata=ResponseMetadata(next_cursor="cur"),
            ),
            UserList(members=[User.model_validate(user(id="U3", name="bob"))]),
        ],
    )

    assert cache.resolve_user("@bob") == "U3"  # found on the second page


# --- Mention substitution ---


def test_substitute_user_mention(mocker: MockerFixture):
    mocker.patch.object(
        client,
        "list_users",
        return_value=UserList(members=[User.model_validate(user(name="alice"))]),
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
                Usergroup(
                    id="S1",
                    team_id="T1",
                    handle="devs",
                    name="Devs",
                    description="",
                    is_external=False,
                    date_delete=0,
                ),
                Usergroup(
                    id="S2",
                    team_id="T1",
                    handle="",  # no usable handle → skipped
                    name="Nameless",
                    description="",
                    is_external=False,
                    date_delete=0,
                ),
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
        return_value=ChannelList(
            channels=[Channel.model_validate(channel(name="general"))]
        ),
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
