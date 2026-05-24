"""コードベース異常検知モジュール。

担当オーナー: 神楽アオイ（監査/QA）
対象モジュール: architect_observer / watchdog / task_health

検知対象:
1. 例外頻発モジュール: 過去1h で ERROR/CRITICAL ログが閾値超のモジュール
2. 起動失敗ループ: 過去1h の dispatcher 再起動が閾値超
3. incidents.jsonl の未クローズ error/critical 件数

architect_observer._detect_signals() から呼ばれる。
"""
from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

JST = timezone(timedelta(hours=9))
BASE_DIR = Path(__file__).parent.parent

INCIDENTS_FILE = BASE_DIR / "company" / "incidents.jsonl"
WATCHDOG_LOG = Path("/tmp/ai_nowa_watchdog.log")

# ログ行パターン: "2026-05-21 20:44:55,164 [ERROR] module_name: message"
_LOG_PATTERN = re.compile(
    r"^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}),\d+ \[(ERROR|CRITICAL|WARNING)\] ([^:]+): (.+)$"
)

ERROR_PER_MODULE_THRESHOLD = 5   # 1h 以内に同一モジュールでこれ以上 → alert
RESTART_LOOP_THRESHOLD = 3       # 1h 以内に dispatcher 再起動がこれ以上 → alert
OPEN_CRITICAL_THRESHOLD = 1      # 未クローズ critical インシデントがこれ以上 → alert


def detect_error_modules(hours: int = 1) -> dict:
    """過去N時間のログから例外頻発モジュールを検知。

    Returns:
        per_module: {module_name: {"error": int, "critical": int, "warning": int}}
        alerts: [{module, count, severity}]
        alert: bool
    """
    if not WATCHDOG_LOG.exists():
        return {"per_module": {}, "alerts": [], "alert": False, "source": "no_log"}

    cutoff = datetime.now(JST) - timedelta(hours=hours)
    per_module: dict[str, Counter] = defaultdict(Counter)

    for line in WATCHDOG_LOG.read_text(encoding="utf-8", errors="replace").splitlines():
        m = _LOG_PATTERN.match(line)
        if not m:
            continue
        ts_str, level, module, _ = m.groups()
        try:
            ts = datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S").replace(tzinfo=JST)
        except ValueError:
            continue
        if ts < cutoff:
            continue
        if level in ("ERROR", "CRITICAL"):
            per_module[module][level.lower()] += 1

    alerts = []
    for module, counts in per_module.items():
        total_errors = counts["error"] + counts["critical"]
        if total_errors >= ERROR_PER_MODULE_THRESHOLD:
            alerts.append({
                "module": module,
                "error": counts["error"],
                "critical": counts["critical"],
                "total": total_errors,
            })

    return {
        "per_module": {k: dict(v) for k, v in per_module.items()},
        "alerts": alerts,
        "alert": len(alerts) > 0,
    }


def detect_restart_loop(hours: int = 1) -> dict:
    """過去N時間の dispatcher 再起動回数を incidents.jsonl から集計。

    Returns:
        restart_count: int
        alert: bool
    """
    if not INCIDENTS_FILE.exists():
        return {"restart_count": 0, "alert": False}

    cutoff = (datetime.now(JST) - timedelta(hours=hours)).isoformat()
    restart_count = 0

    for line in INCIDENTS_FILE.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            e = json.loads(line)
            if e.get("ts", "") < cutoff:
                continue
            if e.get("kind") in ("auto_restart", "dispatcher_down"):
                restart_count += 1
        except json.JSONDecodeError:
            continue

    return {
        "restart_count": restart_count,
        "alert": restart_count >= RESTART_LOOP_THRESHOLD,
    }


def detect_open_incidents(hours: int = 2) -> dict:
    """過去N時間の未クローズ error/critical インシデント数を集計。

    Returns:
        open_incidents: [{ts, kind, severity, detail}]
        alert: bool
    """
    if not INCIDENTS_FILE.exists():
        return {"open_incidents": [], "alert": False}

    cutoff = (datetime.now(JST) - timedelta(hours=hours)).isoformat()
    events = []
    for line in INCIDENTS_FILE.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            e = json.loads(line)
        except json.JSONDecodeError:
            continue
        if e.get("ts", "") >= cutoff:
            events.append(e)

    def _logically_resolved(event_index: int) -> bool:
        """Handle append-only incident logs.

        watchdog writes ``dispatcher_down`` and then ``auto_restart`` as a
        separate resolved event.  Without this relation the health monitor keeps
        reporting a recovered restart as an open incident for the whole window.
        """
        event = events[event_index]
        kind = event.get("kind", "")
        for later in events[event_index + 1:]:
            later_kind = later.get("kind", "")
            later_status = later.get("status", "open")
            if later_status not in {"resolved", "closed"}:
                continue
            if later_kind == f"{kind}_resolved":
                return True
            if kind == "dispatcher_down" and later_kind == "auto_restart":
                return True
            if kind == "auto_restart_failed" and later_kind == "auto_restart":
                return True
        return False

    open_incidents = []

    for idx, e in enumerate(events):
        if e.get("severity") not in ("error", "critical"):
            continue
        if e.get("status", "open") in {"resolved", "closed"}:
            continue
        if _logically_resolved(idx):
            continue
        open_incidents.append({
            "ts": e["ts"][11:19],
            "kind": e.get("kind", "?"),
            "severity": e.get("severity"),
            "detail": e.get("detail", "")[:100],
        })

    return {
        "open_incidents": open_incidents[-10:],
        "alert": len(open_incidents) >= OPEN_CRITICAL_THRESHOLD,
    }


def get_code_health_signals() -> dict:
    """architect_observer._detect_signals() から呼ぶ統合エントリポイント。

    Returns:
        error_modules: detect_error_modules の結果
        restart_loop: detect_restart_loop の結果
        open_incidents: detect_open_incidents の結果
        any_alert: いずれかのアラートが発火しているか
    """
    error_modules = detect_error_modules(hours=1)
    restart_loop = detect_restart_loop(hours=1)
    open_incidents = detect_open_incidents(hours=2)

    return {
        "error_modules": error_modules,
        "restart_loop": restart_loop,
        "open_incidents": open_incidents,
        "any_alert": (
            error_modules["alert"]
            or restart_loop["alert"]
            or open_incidents["alert"]
        ),
    }


if __name__ == "__main__":
    import json as _json
    print(_json.dumps(get_code_health_signals(), ensure_ascii=False, indent=2))
