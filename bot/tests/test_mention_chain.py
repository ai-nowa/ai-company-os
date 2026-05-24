from __future__ import annotations

from bot import mention_chain
from bot.mention_chain import extract_mentions


def test_extract_stale_role_tag_with_adjacent_given_name():
    text = "<@&1505064017046999110> カイ、Bluesky投稿と/about反映をお願いします。"

    assert extract_mentions(text) == ["shirase_kai"]


def test_extract_multiple_unknown_role_tags_from_adjacent_names():
    text = "<@&111> ミオ、公開判断を。 <@&222> ノア、実装の進行管理をお願いします。"

    assert extract_mentions(text) == ["saegusa_mio", "asakura_noa"]


def test_plain_name_without_at_or_role_tag_is_not_a_mention():
    text = "カイに任せるのがよさそうです。ミオも確認したほうがいい。"

    assert extract_mentions(text) == []


def test_high_priority_mentions_do_not_expand_default_parallelism(monkeypatch):
    monkeypatch.setattr(
        mention_chain,
        "_cfg",
        lambda path, default: {
            "mention_chain.max_mentions_per_response": 2,
            "mention_chain.high_priority_mentions_per_response": 2,
        }.get(path, default),
    )

    assert mention_chain.mentions_per_response_limit("[DECISION] 重要判断です") == 2
