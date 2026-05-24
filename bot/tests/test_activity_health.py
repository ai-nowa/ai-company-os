from __future__ import annotations

import json
from datetime import datetime, timedelta

from bot import activity_index, behavior_metrics, code_health_monitor
from bot.config import JST


def _write_jsonl(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows),
        encoding="utf-8",
    )


def test_last_employee_out_uses_recent_archive_and_session_state(tmp_path, monkeypatch):
    monkeypatch.setattr(activity_index, "BASE_DIR", tmp_path)
    emp = tmp_path / "employees" / "arima_reiji" / "session"
    archive = emp / "archive"

    _write_jsonl(
        archive / "conversation_log_2026-05-24T10-00-00+09-00.jsonl",
        [{"ts": "2026-05-24T10:30:00+09:00", "kind": "out", "text": "archived"}],
    )
    _write_jsonl(
        emp / "conversation_log.jsonl",
        [{"ts": "2026-05-24T11:00:00+09:00", "kind": "in", "text": "current input only"}],
    )
    (emp / "session_state.json").write_text(
        json.dumps({"last_active": "2026-05-24T10:45:00+09:00"}),
        encoding="utf-8",
    )

    assert activity_index.last_employee_out_ts("arima_reiji") == "2026-05-24T10:45:00+09:00"


def test_dispatcher_down_is_resolved_by_later_auto_restart(tmp_path, monkeypatch):
    incidents = tmp_path / "incidents.jsonl"
    now = datetime.now(JST)
    _write_jsonl(
        incidents,
        [
            {
                "ts": (now - timedelta(minutes=20)).isoformat(timespec="seconds"),
                "kind": "dispatcher_down",
                "severity": "error",
                "status": "open",
                "detail": "dispatcher process not found",
            },
            {
                "ts": (now - timedelta(minutes=19)).isoformat(timespec="seconds"),
                "kind": "auto_restart",
                "severity": "info",
                "status": "resolved",
                "detail": "new pid=123",
            },
        ],
    )
    monkeypatch.setattr(code_health_monitor, "INCIDENTS_FILE", incidents)

    result = code_health_monitor.detect_open_incidents(hours=2)

    assert result["open_incidents"] == []
    assert result["alert"] is False


def test_sakiokuri_ignores_constructive_wait_context(monkeypatch):
    monkeypatch.setattr(
        behavior_metrics,
        "_load_logs",
        lambda hours: [
            {
                "ts": "2026-05-24T10:00:00+09:00",
                "kind": "out",
                "_emp": "shirase_kai",
                "text": "リツ確認待ちの間に開示文テンプレを作成しました。完了です。",
            },
            {
                "ts": "2026-05-24T10:05:00+09:00",
                "kind": "out",
                "_emp": "kuroba_yuu",
                "text": "これは明日確認します。今日は保留します。",
            },
        ],
    )

    result = behavior_metrics.detect_sakiokuri(hours=24)

    assert result["total_count"] == 1
    assert result["per_employee"] == {"kuroba_yuu": 1}
