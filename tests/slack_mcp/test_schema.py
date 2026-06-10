"""Tests for slack.schema — the empty-dropping serializer and field curation.

Beyond the base serializer, these assert that the typed submodels (ChannelText,
Reaction, Profile, and the reused Channel) keep only their declared fields, so
Slack's bloaty extras (image_* sizes, reactor lists, topic creator/last_set)
never reach an MCP response.
"""

from slack_mcp.schema.channel import Channel, ChannelList
from slack_mcp.schema.message import Message
from slack_mcp.schema.search import SearchResult
from slack_mcp.schema.user import User


def test_drop_none_omits_null_keys():
    dumped = Channel(id="C1").model_dump()

    assert dumped == {"id": "C1"}  # every other field is None and dropped


def test_drop_none_keeps_empty_collections():
    dumped = ChannelList().model_dump()

    assert dumped == {"channels": []}  # [] kept; response_metadata (None) dropped


def test_drops_empty_string_and_collapsed_submodel():
    # "" and a submodel that prunes to {} are dropped; recursion collapses empties.
    ch = Channel.model_validate({"id": "C1", "name": "", "topic": {"value": ""}})

    assert ch.model_dump() == {"id": "C1"}  # name="" gone; topic -> {} -> gone


def test_keeps_zero_and_false():
    # 0 / False are definite states (not "absent") and survive the prune.
    ch = Channel.model_validate({"id": "C1", "num_members": 0, "is_private": False})

    assert ch.model_dump() == {"id": "C1", "num_members": 0, "is_private": False}


def test_channel_topic_keeps_only_value():
    ch = Channel.model_validate(
        {"id": "C1", "topic": {"value": "hi", "creator": "U1", "last_set": 1}}
    )

    assert ch.topic is not None
    assert ch.topic.model_dump() == {"value": "hi"}  # creator / last_set dropped


def test_message_reactions_drop_users():
    msg = Message.model_validate(
        {"reactions": [{"name": "tada", "count": 2, "users": ["U1", "U2"]}]}
    )

    assert msg.reactions is not None
    assert msg.reactions[0].model_dump() == {
        "name": "tada",
        "count": 2,
    }  # users dropped


def test_user_profile_curated_to_subset():
    user = User.model_validate(
        {"id": "U1", "profile": {"display_name": "al", "image_512": "x", "phone": "p"}}
    )

    assert user.profile is not None
    assert user.profile.model_dump() == {"display_name": "al"}  # extras dropped


def test_search_match_channel_uses_channel_model():
    result = SearchResult.model_validate(
        {"messages": {"matches": [{"channel": {"id": "C1", "name": "g"}}]}}
    )

    assert result.messages is not None
    match = result.messages.matches[0]
    assert match.channel is not None
    assert match.channel.id == "C1"
    assert match.channel.name == "g"
