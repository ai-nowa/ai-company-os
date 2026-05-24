from __future__ import annotations

import json

import bot.external_metrics as em
from bot.architect_outbox import submit_post
import bot.architect_outbox as architect_outbox


def test_count_intent_entries_drops_pii_and_counts_recent():
    entries = [
        {"email": "a@example.com", "intent": "yes", "ts": em.now_jst_iso()},
        {"email": "b@example.com", "intent": "maybe", "ts": "2020-01-01T00:00:00+09:00"},
        {"email": "c@example.com", "intent": "unknown", "ts": "2020-01-01T00:00:00+09:00"},
    ]

    counts = em._count_intent_entries(entries)

    assert counts["total"] == 3
    assert counts["yes"] == 1
    assert counts["maybe"] == 1
    assert counts["other"] == 1
    assert counts["recent_24h"] == 1
    assert counts["contains_pii"] is False
    assert "email" not in counts


def test_external_digest_uses_snapshot_without_network(monkeypatch, tmp_path):
    snapshot = {
        "ts": "2026-05-24T12:00:00+09:00",
        "revenue": {"available": True, "order_count": 0, "gross_jpy": 0},
        "traffic": {"ga4": {"available": True, "pageviews_today": 9, "shop_pageviews_today": 3, "about_pageviews_today": 1}},
        "intent": {"purchase_form": {"available": True, "total": 2, "yes": 1, "maybe": 1, "recent_24h": 2}},
        "youtube": {"available": False, "unavailable_reason": "missing scope"},
        "site": {"shop_live": {"available": True, "title": "AI NOWA OS Starter Kit v0.1", "price": "¥2,980"}},
        "health": {"shop_local_live_mismatch": False, "unavailable": {"youtube": "missing scope"}},
    }
    path = tmp_path / "snapshot.json"
    path.write_text(json.dumps(snapshot), encoding="utf-8")
    monkeypatch.setattr(em, "SNAPSHOT_PATH", path)

    digest = "\n".join(em.external_digest_items())

    assert "GA4 today: PV=9" in digest
    assert "intent form: total=2" in digest
    assert "shop local/live mismatch: False" in digest
    assert "missing scope" in digest


def test_youtube_analytics_row_to_metrics_handles_empty_rows():
    metrics = ["views", "estimatedMinutesWatched", "averageViewDuration"]

    result = em._youtube_analytics_row_to_metrics({"rows": []}, metrics)

    assert result == {
        "views": 0,
        "estimatedMinutesWatched": 0,
        "averageViewDuration": 0,
    }


def test_youtube_analytics_row_to_metrics_maps_headers():
    response = {
        "columnHeaders": [
            {"name": "views"},
            {"name": "averageViewDuration"},
            {"name": "estimatedMinutesWatched"},
        ],
        "rows": [[12, 34, 56]],
    }

    result = em._youtube_analytics_row_to_metrics(
        response,
        ["views", "estimatedMinutesWatched", "averageViewDuration", "likes"],
    )

    assert result == {
        "views": 12,
        "estimatedMinutesWatched": 56,
        "averageViewDuration": 34,
        "likes": 0,
    }


def test_architect_outbox_label_is_filename_safe(monkeypatch, tmp_path):
    monkeypatch.setattr(architect_outbox, "OUTBOX_DIR", tmp_path)

    path = submit_post("お知らせ", "test", label="self_improvement_anticipation_check:日程:07/08")

    assert path.parent == tmp_path
    assert "/" not in path.name
    assert path.exists()
