from __future__ import annotations

from bot.context_assembler import assemble_state_digest
from bot.output_routes import output_route_items, route_for_kind


def test_output_routes_include_concrete_site_deploy_command():
    text = "\n".join(output_route_items(max_chars=2000))

    assert "wrangler pages deploy public" in text
    assert "site/public/notes" in text
    assert "いくと依頼" in text


def test_state_digest_includes_output_routes_for_routine():
    digest = assemble_state_digest("hoshino_ritsu", "記事公開", mode="routine")

    assert "Output Routes" in digest
    assert "wrangler pages deploy public" in digest
    assert "投稿/公開/確認をいくとへ依頼しない" in digest


def test_release_route_for_x_avoids_human_wait():
    action = route_for_kind("x_post")

    assert "X待ち禁止" in action
    assert "bluesky_client" in action
