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


def test_channel_im_variant_keeps_user():
    # conversations.open returns an IM: `user` is its identity, `priority` is noise.
    ch = Channel.model_validate(
        {"id": "D1", "is_im": True, "created": 1, "user": "U9", "priority": 0.5}
    )

    assert ch.user == "U9"
    assert "priority" not in ch.model_dump()


def test_channel_mpim_flag_kept():
    ch = Channel.model_validate(channel(is_im=False, is_mpim=True, is_private=True))

    assert ch.is_mpim is True


def test_message_files_parsed():
    msg = Message.model_validate(
        message(files=[{"id": "F1", "name": "img.png", "mimetype": "image/png"}])
    )

    assert msg.files is not None
    assert len(msg.files) == 1
    assert isinstance(msg.files[0], File)
    assert msg.files[0].id == "F1"
    assert msg.files[0].mimetype == "image/png"


def test_message_blocks_and_attachments_passthrough():
    # Bot/app messages leave top-level text empty and carry content in Block Kit
    # blocks / attachments — these must survive verbatim, not be dropped.
    msg = Message.model_validate(
        message(
            text="",
            blocks=[{"type": "section", "text": {"type": "mrkdwn", "text": "hi"}}],
            attachments=[{"id": 1, "fallback": "alert", "text": "detail"}],
        )
    )

    dumped = msg.model_dump()
    assert dumped["blocks"] == [
        {"type": "section", "text": {"type": "mrkdwn", "text": "hi"}}
    ]
    assert dumped["attachments"] == [{"id": 1, "fallback": "alert", "text": "detail"}]


def test_message_denylist_drops_bloat_keeps_content():
    msg = Message.model_validate(
        message(
            bot_id="B1",
            username="Datadog",
            attachments=[{"id": 1, "title": "CPU"}],
            client_msg_id="dedup",
            team="T1",
            icons={"image_48": "http://x"},
            bot_profile={"id": "B1", "name": "Datadog"},
            reply_users=["U1", "U2"],
            subscribed=True,
        )
    )

    dumped = msg.model_dump()
    assert dumped["username"] == "Datadog"
    assert dumped["attachments"] == [{"id": 1, "title": "CPU"}]
    for junk in (
        "client_msg_id",
        "team",
        "icons",
        "bot_profile",
        "reply_users",
        "subscribed",
    ):
        assert junk not in dumped


def test_message_extra_allow_keeps_unknown_fields():
    # Undeclared, non-bloat fields survive as raw — no silent loss on the open,
    # evolving message surface (future/rare fields, subtype payloads we skip).
    msg = Message.model_validate(
        message(comment={"comment": "nice"}, permalink="http://p", edited={"ts": "1"})
    )

    dumped = msg.model_dump()
    assert dumped["comment"] == {"comment": "nice"}
    assert dumped["permalink"] == "http://p"
    assert dumped["edited"] == {"ts": "1"}


def test_message_subtype_content_surfaced():
    # channel_topic's content lives in `topic`; the old allowlist dropped it.
    msg = Message.model_validate(
        message(subtype="channel_topic", user="U1", topic="새 토픽")
    )

    dumped = msg.model_dump()
    assert dumped["subtype"] == "channel_topic"
    assert dumped["topic"] == "새 토픽"


def test_denylist_is_message_local_not_base():
    # The denylist lives in Message's serializer only — the base serializer has
    # no notion of it. An open model that is *not* Message keeps fields named
    # like Message-bloat, proving the rule didn't leak into the base.
    from pydantic import ConfigDict

    from slack_mcp.schema.base import SlackModel

    class Other(SlackModel):
        model_config = ConfigDict(extra="allow")

    dumped = Other.model_validate({"team": "T1", "client_msg_id": "z"}).model_dump()

    assert dumped == {"team": "T1", "client_msg_id": "z"}  # base has no denylist


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


def test_search_match_channel_without_created():
    # search.messages' channel object omits `created`; parsing must not require it.
    result = SearchResult.model_validate(
        {"messages": {"matches": [{"channel": {"id": "C1", "is_im": False}}]}}
    )

    assert result.messages is not None
    assert result.messages.matches[0].channel is not None
    assert result.messages.matches[0].channel.created is None
