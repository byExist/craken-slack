"""Tests for slack.schema — the empty-dropping serializer and field curation.

Beyond the base serializer, these assert that the typed submodels (ChannelText,
Reaction, Profile, and the reused Channel) keep only their declared fields, so
Slack's bloaty extras (image_* sizes, reactor lists, topic creator/last_set)
never reach an MCP response.
"""

from slack_mcp.schema.channel import Channel, ChannelList
from slack_mcp.schema.file import File
from slack_mcp.schema.message import Message
from slack_mcp.schema.search import SearchResult
from slack_mcp.schema.user import User
from support import channel, message, profile, user


def test_drop_none_omits_null_keys():
    dumped = Channel(id="C1", is_im=False, created=0).model_dump()

    # name / topic / … are None and dropped; only present fields remain.
    assert dumped == {"id": "C1", "is_im": False, "created": 0}


def test_drop_none_keeps_empty_collections():
    dumped = ChannelList().model_dump()

    assert dumped == {"channels": []}  # [] kept; response_metadata (None) dropped


def test_keeps_zero_and_false():
    # 0 / False are definite states (not "absent") and survive the prune.
    ch = Channel.model_validate(channel(num_members=0, is_private=False))

    assert ch.model_dump() == {
        "id": "C1",
        "is_im": False,
        "created": 0,
        "num_members": 0,
        "is_private": False,
    }


def test_channel_topic_keeps_only_value():
    ch = Channel.model_validate(
        channel(topic={"value": "hi", "creator": "U1", "last_set": 1})
    )

    assert ch.topic is not None
    assert ch.topic.model_dump() == {"value": "hi"}  # creator / last_set dropped


def test_message_files_parsed():
    msg = Message.model_validate(
        message(files=[{"id": "F1", "name": "img.png", "mimetype": "image/png"}])
    )

    assert msg.files is not None
    assert len(msg.files) == 1
    assert isinstance(msg.files[0], File)
    assert msg.files[0].id == "F1"
    assert msg.files[0].mimetype == "image/png"


def test_message_reactions_drop_users():
    msg = Message.model_validate(
        {
            "type": "message",
            "text": "",
            "ts": "1.1",
            "reactions": [{"name": "tada", "count": 2, "users": ["U1", "U2"]}],
        }
    )

    assert msg.reactions is not None
    assert msg.reactions[0].model_dump() == {
        "name": "tada",
        "count": 2,
    }  # users dropped


def test_message_user_profile_curated_to_naming_subset():
    msg = Message.model_validate(
        {
            "type": "message",
            "text": "hi",
            "ts": "1.1",
            "user": "U1",
            "user_profile": {
                "name": "alice",
                "real_name": "Alice Kim",
                "display_name": "al",
                "avatar_hash": "abc",
                "image_72": "https://x",
                "is_restricted": False,
            },
        }
    )

    assert msg.user_profile is not None
    assert msg.user_profile.model_dump() == {
        "name": "alice",
        "real_name": "Alice Kim",
        "display_name": "al",
    }  # avatar_hash / image_72 / is_restricted dropped


def test_user_profile_curated_to_subset():
    u = User.model_validate(
        user(profile=profile(display_name="al", image_512="x", phone="p"))
    )

    assert u.profile is not None
    # image_512 / phone (not declared) dropped; the declared subset kept.
    assert u.profile.model_dump() == {
        "display_name": "al",
        "real_name": "",
        "title": "",
        "status_text": "",
        "status_emoji": "",
    }


def test_search_match_channel_uses_channel_model():
    result = SearchResult.model_validate(
        {"messages": {"matches": [{"channel": channel(name="g")}]}}
    )

    assert result.messages is not None
    match = result.messages.matches[0]
    assert match.channel is not None
    assert match.channel.id == "C1"
    assert match.channel.name == "g"
