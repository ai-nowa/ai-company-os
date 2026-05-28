from __future__ import annotations

import json
from pathlib import Path

import bot.release_board as rb
import bot.shipped_artifacts as sa


def _redirect_release_paths(monkeypatch, tmp_path: Path) -> Path:
    base = tmp_path
    company = base / "company"
    discord_log = company / "discord_log"
    employees = base / "employees"
    monkeypatch.setattr(rb, "BASE_DIR", base)
    monkeypatch.setattr(rb, "COMPANY_DIR", company)
    monkeypatch.setattr(rb, "EMPLOYEES_DIR", employees)
    monkeypatch.setattr(rb, "DISCORD_LOG_DIR", discord_log)
    monkeypatch.setattr(rb, "IKUTO_REQ_LOG", discord_log / "📥｜いくと依頼.jsonl")
    monkeypatch.setattr(rb, "OUTPUT_PATH", company / "release_board.md")
    monkeypatch.setattr(rb, "STATE_FILE", company / ".release_pressure_state.json")
    monkeypatch.setattr(sa, "LEDGER_PATH", company / "shipped_artifacts.jsonl")
    company.mkdir(parents=True, exist_ok=True)
    discord_log.mkdir(parents=True, exist_ok=True)
    return base


def test_release_board_counts_public_urls_and_ready_candidates(monkeypatch, tmp_path):
    base = _redirect_release_paths(monkeypatch, tmp_path)
    outbox = base / "employees" / "kuroba_yuu" / "outbox"
    outbox.mkdir(parents=True, exist_ok=True)
    (outbox / "2026-05-24_exp005_x_post_v01.md").write_text(
        "# EXP-005 Xポスト\n\n投稿本文（コピペOK）:\nAIにも、コンディションがある。\nai-nowa.com/about\n",
        encoding="utf-8",
    )
    (rb.DISCORD_LOG_DIR / "🎯｜経営会議.jsonl").write_text(
        json.dumps(
            {
                "ts": rb.now_jst_iso(),
                "kind": "employee",
                "author": "白瀬カイ",
                "text": "Production: https://ai-nowa.com/shop/",
            },
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )

    metrics = rb.collect_release_metrics()

    assert metrics["public_outputs_24h"] == 1
    assert metrics["ready_to_ship_count"] == 1
    assert metrics["top_candidates"][0]["kind"] == "x_post"


def test_human_wait_requests_become_release_debt(monkeypatch, tmp_path):
    _redirect_release_paths(monkeypatch, tmp_path)
    rb.IKUTO_REQ_LOG.write_text(
        json.dumps(
            {
                "ts": rb.now_jst_iso(),
                "kind": "employee",
                "author": "黒羽ユウ",
                "employee_id": "kuroba_yuu",
                "text": "X投稿をお願いします。投稿本文はコピペOKです。",
            },
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )

    metrics = rb.collect_release_metrics()

    assert metrics["public_outputs_24h"] == 0
    assert metrics["human_wait_requests_24h"] == 1
    assert metrics["output_debt"] == 1
    assert "人間待ち" in rb.render_release_board(metrics)


def test_release_digest_is_compact_and_actionable(monkeypatch, tmp_path):
    base = _redirect_release_paths(monkeypatch, tmp_path)
    outbox = base / "employees" / "hoshino_ritsu" / "outbox"
    outbox.mkdir(parents=True, exist_ok=True)
    (outbox / "2026-05-24_article09_draft.md").write_text(
        "# article-09\n\n公開依頼。記事本文ドラフト。ai-nowa.com/shop へ誘導する。\n",
        encoding="utf-8",
    )

    digest = rb.release_digest(max_chars=500, employee_id="hoshino_ritsu")

    assert len(digest) <= 500
    assert "public_outputs_24h" in digest
    assert "ready:" in digest
    assert "shared/templates/output_playbook.md" in digest


def test_internal_review_files_are_excluded(monkeypatch, tmp_path):
    base = _redirect_release_paths(monkeypatch, tmp_path)
    outbox = base / "employees" / "arima_reiji" / "outbox"
    outbox.mkdir(parents=True, exist_ok=True)
    (outbox / "2026-05-24_exp002_eod_pm_ack_ceo.md").write_text(
        "# EOD ACK\n\nCEO決定。投稿本文ではない。Xポストの判定。\n",
        encoding="utf-8",
    )
    (outbox / "2026-05-24_handover_note.md").write_text(
        "# 引き継ぎノート\n\n投稿本文。YouTube。\n",
        encoding="utf-8",
    )
    (outbox / "2026-05-24_exp002_phase_restructure.md").write_text(
        "# Phase restructure\n\n投稿依頼。\n",
        encoding="utf-8",
    )

    metrics = rb.collect_release_metrics()
    paths = [c["path"] for c in metrics["top_candidates"]]
    assert all("eod_pm_ack" not in p for p in paths)
    assert all("handover_note" not in p for p in paths)
    assert all("phase_restructure" not in p for p in paths)


def test_duplicate_topic_is_superseded_by_public_url(monkeypatch, tmp_path):
    base = _redirect_release_paths(monkeypatch, tmp_path)
    outbox = base / "employees" / "kuroba_yuu" / "outbox"
    outbox.mkdir(parents=True, exist_ok=True)
    (outbox / "2026-05-24_exp005_x_post_ai_condition_v01.md").write_text(
        "# EXP-005\n\n投稿本文（コピペOK）:\nAIにも、コンディションがある。\n",
        encoding="utf-8",
    )
    (rb.DISCORD_LOG_DIR / "📦｜成果物報告.jsonl").write_text(
        json.dumps(
            {
                "ts": rb.now_jst_iso(),
                "kind": "employee",
                "author": "黒羽ユウ",
                "text": "ai-condition公開 https://ai-nowa.com/notes/ai-condition/",
            },
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )

    metrics = rb.collect_release_metrics()
    assert metrics["public_outputs_24h"] == 1
    assert metrics["superseded_count"] >= 1
    assert metrics["ready_to_ship_count"] == 0


def test_quiet_hours_detection_window(monkeypatch):
    from datetime import datetime
    from bot.config import JST

    assert rb._is_quiet_hours(datetime(2026, 5, 24, 22, 30, tzinfo=JST))
    assert rb._is_quiet_hours(datetime(2026, 5, 25, 6, 59, tzinfo=JST))
    assert not rb._is_quiet_hours(datetime(2026, 5, 25, 7, 0, tzinfo=JST))
    assert not rb._is_quiet_hours(datetime(2026, 5, 24, 21, 59, tzinfo=JST))


def test_series_arc_and_series_entry_are_excluded(monkeypatch, tmp_path):
    base = _redirect_release_paths(monkeypatch, tmp_path)
    outbox = base / "employees" / "hoshino_ritsu" / "outbox"
    outbox.mkdir(parents=True, exist_ok=True)
    (outbox / "series_arc.md").write_text(
        "# Series Arc\n\nYouTube シリーズ管理台帳。投稿本文ではない。\n",
        encoding="utf-8",
    )
    (outbox / "2026-05-27_series_entry_ep05.md").write_text(
        "# Series Entry ep05\n\nYouTube。シリーズ管理エントリ。\n",
        encoding="utf-8",
    )

    metrics = rb.collect_release_metrics()
    paths = [c["path"] for c in metrics["top_candidates"]]
    assert all("series_arc" not in p for p in paths), f"series_arc が ready に残っている: {paths}"
    assert all("series_entry" not in p for p in paths), f"series_entry が ready に残っている: {paths}"


def test_untracked_published_articles_detected_and_shipped_excluded(monkeypatch, tmp_path):
    base = _redirect_release_paths(monkeypatch, tmp_path)
    articles_dir = base / "site" / "public" / "articles"
    articles_dir.mkdir(parents=True, exist_ok=True)
    # index に 14, 15 が載っている（両方とも公開済み）
    (articles_dir / "index.html").write_text(
        '<a href="article-14/">#002</a><a href="article-15/">#003</a>',
        encoding="utf-8",
    )
    # shipped には 15 のみ記録（14 は台帳遡及漏れ＝幽霊在庫）
    ledger = base / "company" / "shipped_artifacts.jsonl"
    ledger.parent.mkdir(parents=True, exist_ok=True)
    ledger.write_text(
        json.dumps({
            "route": "article",
            "source_path": "employees/hoshino_ritsu/outbox/x.md",
            "output_url": "https://ai-nowa.com/articles/article-15/",
            "ts": "2026-05-28T00:00:00+09:00",
        }, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    untracked = rb.detect_untracked_published_articles()
    assert "article-14" in untracked, f"未記録の article-14 が検出されていない: {untracked}"
    assert "article-15" not in untracked, f"記録済みの article-15 が誤検出された（二重記録防止）: {untracked}"


def test_freeze_guard_marker_excludes_draft_from_ready(monkeypatch, tmp_path):
    base = _redirect_release_paths(monkeypatch, tmp_path)
    outbox = base / "employees" / "kuroba_yuu" / "outbox"
    outbox.mkdir(parents=True, exist_ok=True)
    # 公開語(投稿本文/コピペOK)を持つが、本文の凍結ガードで温存中のドラフト
    (outbox / "2026-05-28_next_branch_revenue_board_draft.md").write_text(
        "# Next Branch 収益ボード draft\n"
        "status: 温存のみ（非公開）\n"
        "凍結ガード: 規約確定までこのdraftは公開しない\n\n"
        "投稿本文（コピペOK）:\nshop 販売導線のCTA案。\n",
        encoding="utf-8",
    )
    metrics = rb.collect_release_metrics()
    paths = [c["path"] for c in metrics["top_candidates"]]
    assert all("next_branch_revenue_board" not in p for p in paths), (
        f"凍結ガード付き draft が ready に残っている: {paths}"
    )
    assert metrics["ready_to_ship_count"] == 0


def test_freeze_guard_does_not_over_exclude_ready_status(monkeypatch, tmp_path):
    base = _redirect_release_paths(monkeypatch, tmp_path)
    outbox = base / "employees" / "kuroba_yuu" / "outbox"
    outbox.mkdir(parents=True, exist_ok=True)
    # status: が公開可（ready）を指す場合は除外しない（誤除外防止）
    (outbox / "2026-05-28_cta_copy_ready.md").write_text(
        "# CTA コピー\n"
        "status: ready（公開OK）\n\n"
        "投稿本文（コピペOK）:\nai-nowa.com/shop へ。\n",
        encoding="utf-8",
    )
    metrics = rb.collect_release_metrics()
    paths = [c["path"] for c in metrics["top_candidates"]]
    assert any("cta_copy_ready" in p for p in paths), (
        f"公開可ステータスの draft が誤って除外された: {paths}"
    )


def test_draft_without_freeze_guard_stays_ready(monkeypatch, tmp_path):
    base = _redirect_release_paths(monkeypatch, tmp_path)
    outbox = base / "employees" / "kuroba_yuu" / "outbox"
    outbox.mkdir(parents=True, exist_ok=True)
    # 凍結マーカーが無い通常の公開draftは従来どおり ready に残る（偽陰性=正規ページ誤除外の監査）
    (outbox / "2026-05-28_shop_cta_draft.md").write_text(
        "# shop CTA draft\n\n投稿本文（コピペOK）:\nai-nowa.com/shop の販売導線CTA。\n",
        encoding="utf-8",
    )
    metrics = rb.collect_release_metrics()
    paths = [c["path"] for c in metrics["top_candidates"]]
    assert any("shop_cta_draft" in p for p in paths), (
        f"マーカー無しの公開draftが誤って除外された: {paths}"
    )
    assert metrics["ready_to_ship_count"] == 1


def test_human_required_internal_request_excluded_from_ready(monkeypatch, tmp_path):
    # [HUMAN_REQUIRED] の内部人間依頼ドキュメントは、公開語(deploy/販売/導線)を含んでも
    # Ready(公開候補)に計上しない。構造ゲートの遡及漏れ修正(2026-05-28 ミオ報告)の回帰テスト。
    base = _redirect_release_paths(monkeypatch, tmp_path)
    outbox = base / "employees" / "shirase_kai" / "outbox"
    outbox.mkdir(parents=True, exist_ok=True)
    (outbox / "2026-05-28_ga4_reauth_request.md").write_text(
        "# [HUMAN_REQUIRED] GA4 再認証依頼（外部KPI取得が停止中）\n\n"
        "ブラウザ承認が必要。deploy 後に販売導線の計測が戻る。投稿本文（コピペOK）相当の素材ではない。\n",
        encoding="utf-8",
    )
    metrics = rb.collect_release_metrics()
    paths = [c["path"] for c in metrics["top_candidates"]]
    assert all("ga4_reauth_request" not in p for p in paths), (
        f"[HUMAN_REQUIRED] 内部依頼が ready に誤計上されている: {paths}"
    )


def test_human_wait_filter_does_not_over_exclude_kopipe_ok(monkeypatch, tmp_path):
    # 衝突ガード: "コピペ"(HUMAN_WAIT) ⊂ "コピペOK"(READY) のため、
    # [HUMAN_REQUIRED] を持たない正当な「コピペOK」公開draftは ready に残る。
    base = _redirect_release_paths(monkeypatch, tmp_path)
    outbox = base / "employees" / "kuroba_yuu" / "outbox"
    outbox.mkdir(parents=True, exist_ok=True)
    (outbox / "2026-05-28_ep03_about_cta_ready.md").write_text(
        "# ep03 説明欄 CTA\n\n誘導ブロック（コピペOK）:\nai-nowa.com/about へ誘導する説明欄。\n",
        encoding="utf-8",
    )
    metrics = rb.collect_release_metrics()
    paths = [c["path"] for c in metrics["top_candidates"]]
    assert any("ep03_about_cta_ready" in p for p in paths), (
        f"コピペOK の公開draftが人間待ちフィルタで誤除外された: {paths}"
    )


def test_human_required_classified_as_human_auth_not_reusable(monkeypatch):
    # [HUMAN_REQUIRED](本人認証/権限が必須)は human_auth に分類され、
    # x_post等の公開kindへ誤分類して「Bluesky転用」を提案してはならない。
    # GA4再認証が x_post 誤分類→転用提案された事例(2026-05-28 黒羽報告)の回帰テスト。
    text = "# [HUMAN_REQUIRED] GA4 OAuth再認証依頼（いくと宛）\nブラウザ承認待ち"
    assert rb._wait_kind(text) == "human_auth"
    # 紛らわしく "X" や "投稿" を含んでも human_auth が優先される
    assert rb._wait_kind("[HUMAN_REQUIRED] X投稿の前に本人確認が必要") == "human_auth"
    action = rb._suggest_action("human_auth", "x.md", text)
    assert "転用" in action and "不可" in action
    assert "Bluesky" not in action or "不可" in action


def test_wait_kind_normal_x_post_unchanged(monkeypatch):
    # 通常の公開依頼は従来どおり x_post / video に分類される（誤って human_auth に倒さない）。
    assert rb._wait_kind("EXP-005 Xポスト 投稿本文（コピペOK）") == "x_post"
    assert rb._wait_kind("YouTube Shorts 動画の公開をお願いします") == "video"


def test_has_freeze_guard_unit():
    assert rb.has_freeze_guard("status: 温存のみ（非公開）")
    assert rb.has_freeze_guard("凍結ガード: 公開しない")
    assert rb.has_freeze_guard("- 凍結ガード： 規約確定まで deployしない")
    assert not rb.has_freeze_guard("status: ready")
    assert not rb.has_freeze_guard("公開依頼。投稿本文はコピペOK。")


def test_has_freeze_guard_internal_visibility():
    # 行頭メタの visibility 宣言は降格する(internal/社内/非公開/private、全角コロン、リストマーカー許容)。
    assert rb.has_freeze_guard("- visibility: **internal**（社内運用文書）")
    assert rb.has_freeze_guard("visibility：社内")
    assert rb.has_freeze_guard("> visibility: private")
    # 本文中の言及や否定文脈は誤除外しない(行頭アンカー+値限定の効果)。
    assert not rb.has_freeze_guard("これは公開対象外ではない。視聴者向けに公開する。")
    assert not rb.has_freeze_guard("`visibility: internal` と本文に明記した文書が誤計上される")
    assert not rb.has_freeze_guard("visibility: public")
