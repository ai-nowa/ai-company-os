from __future__ import annotations

from bot.owner_request_policy import (
    OWNER_REQUEST_MARKER,
    build_redirect_notice,
    evaluate_owner_request,
    should_allow_owner_request,
    should_redirect_owner_request,
)


def test_routine_publish_request_to_owner_is_redirected():
    text = "article-10を公開してください。パス: employees/hoshino_ritsu/outbox/article10.md"

    assert should_redirect_owner_request("📥｜いくと依頼", text) is True


def test_stale_youtube_oauth_request_is_redirected_when_route_exists(monkeypatch):
    from bot import output_routes

    monkeypatch.setattr(
        output_routes,
        "route_preflight_for_text",
        lambda _text: {
            "route": "youtube",
            "available": True,
            "command": "python -m bot.youtube_upload",
            "preflight": ["bot/youtube_token.json exists"],
            "fallback": "site note",
        },
    )
    text = f"{OWNER_REQUEST_MARKER} YouTube OAuth の認証コード入力だけお願いします。"

    assert should_allow_owner_request(text) is False
    assert should_redirect_owner_request("📥｜いくと依頼", text) is True


def test_human_required_auth_failure_can_pass(monkeypatch):
    from bot import output_routes

    monkeypatch.setattr(
        output_routes,
        "route_preflight_for_text",
        lambda _text: {
            "route": "youtube",
            "available": True,
            "command": "python -m bot.youtube_upload",
            "preflight": ["bot/youtube_token.json exists"],
            "fallback": "site note",
        },
    )
    text = f"{OWNER_REQUEST_MARKER} YouTube OAuth refresh failed。再認証コード入力だけお願いします。"

    assert should_allow_owner_request(text) is True
    assert should_redirect_owner_request("📥｜いくと依頼", text) is False


def test_human_required_oauth_failure_passes_for_any_route(monkeypatch):
    """GA4 OAuth 等、youtube 以外の route が available と判定されても、
    HUMAN_REQUIRED + hard_human_keyword + auth_failure_keyword なら通る。
    過去の line 97 youtube限定 bug の回帰防止。
    """
    from bot import output_routes

    monkeypatch.setattr(
        output_routes,
        "route_preflight_for_text",
        lambda _text: {
            "route": "note",
            "available": True,
            "command": "create note html",
            "preflight": ["site/public/notes/<slug>/index.html を作成"],
            "fallback": "Discord公開報告へ転用",
        },
    )
    text = (
        f"{OWNER_REQUEST_MARKER} GA4 OAuth同意画面を「本番環境」に昇格してください。"
        "tokenが2.5日で失効するchurnを構造で止める。"
    )

    decision = evaluate_owner_request(text)
    assert decision.allowed is True
    assert decision.reason == "explicit_human_only_auth_failure"
    assert should_redirect_owner_request("📥｜いくと依頼", text) is False


def test_marker_without_hard_human_keyword_is_still_redirected():
    text = f"{OWNER_REQUEST_MARKER} Xに投稿してください。"

    assert should_redirect_owner_request("📥｜いくと依頼", text) is True


def test_redirect_notice_removes_direct_owner_addressing():
    notice = build_redirect_notice("@いくと X投稿お願いします。", "黒羽ユウ")

    assert "@いくと" not in notice
    assert "OWNER_REQUEST_BLOCKED" in notice


def test_routeable_article_request_returns_preflight(monkeypatch):
    from bot import output_routes

    monkeypatch.setattr(
        output_routes,
        "route_preflight_for_text",
        lambda _text: {
            "route": "article",
            "available": True,
            "command": "update article html",
            "preflight": ["MD->HTML変換", "記事一覧更新"],
            "fallback": "site note",
        },
    )
    decision = evaluate_owner_request("article-10を公開してください。")

    assert decision.allowed is False
    assert decision.route == "article"
    assert "MD->HTML" in "\n".join(decision.checks)
