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
