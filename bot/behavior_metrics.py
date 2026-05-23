"""馴れ合い率・先送り発言数 の検知モジュール。

architect_observer.py の _detect_signals() から呼ばれる、または
self_improvement_loop.py のトリガー評価で使用。

検知定義:
- nareai_rate: 過去N時間の承認発言率。成果物ゼロ継続中に高率なら警告
- sakiokuri_count: 過去N時間の先送り発言数。5件/日超で警告
"""
from __future__ import annotations

import glob
import json
import re
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

JST = timezone(timedelta(hours=9))

BASE_DIR = Path(__file__).parent.parent
EMPLOYEE_IDS = [
    "arima_reiji",
    "asakura_noa",
    "hinata_nagi",
    "hoshino_ritsu",
    "kagura_aoi",
    "kuroba_yuu",
    "morinaga_haru",
    "saegusa_mio",
    "shirase_kai",
]

NAREAI_KEYWORDS: list[str] = [
    "了解", "ありがとう", "感謝", "確認しました", "承知",
    "問題ありません", "受領しました", "いいですね", "助かります",
    "よかった", "拝承", "なるほど", "その通り", "大丈夫です",
    "お疲れ", "ありがとうございます",
]

SAKIOKURI_PATTERNS: list[str] = [
    r"後で",
    r"後ほど",
    r"後日",
    r"いずれ",
    r"保留",
    r"一旦",
    r"いったん",
    r"明日(また|以降|確認)",
    r"来週",
    r"次回",
    r"次のフェーズ",
    r"Phase\s*\d+\s*以降",
    r"[^\S]待ち[^\S]",  # 「〜待ち」（文脈: ブロックされている）
    r"が決まってから",
    r"確定してから",
    r"余裕(が|でき)[たら]",
    r"とりあえず",
    r"48時間",   # Architectが禁止した言葉
    r"明日朝",
]

NAREAI_RATE_THRESHOLD = 0.60
NAREAI_NO_OUTPUT_HOURS = 3
SAKIOKURI_DAILY_THRESHOLD = 5


def _load_logs(hours: int) -> list[dict]:
    """指定時間以内のログエントリを全社員分取得。"""
    cutoff = (datetime.now(JST) - timedelta(hours=hours)).isoformat()
    entries: list[dict] = []
    for f in glob.glob(str(BASE_DIR / "employees/*/session/conversation_log.jsonl")):
        emp_id = Path(f).parent.parent.name
        try:
            for line in Path(f).read_text(encoding="utf-8", errors="replace").splitlines():
                try:
                    e = json.loads(line)
                    if e.get("ts", "") < cutoff:
                        continue
                    e["_emp"] = emp_id
                    entries.append(e)
                except json.JSONDecodeError:
                    continue
        except OSError:
            continue
    return entries


def _has_output_files(emp_id: str, hours: int) -> bool:
    """社員が指定時間内にoutboxへファイルを出力したか確認。"""
    cutoff = datetime.now(JST) - timedelta(hours=hours)
    outbox = BASE_DIR / "employees" / emp_id / "outbox"
    if not outbox.exists():
        return False
    for f in outbox.rglob("*"):
        if f.is_file():
            mtime = datetime.fromtimestamp(f.stat().st_mtime, tz=JST)
            if mtime >= cutoff:
                return True
    return False


def detect_nareai(hours: int = 3) -> dict:
    """馴れ合い率の検知。

    Returns:
        nareai_rate: float (0.0-1.0)
        approval_count: int
        total_count: int
        per_employee: {emp_id: {"approval": int, "total": int, "no_output": bool}}
        alerts: list[{emp_id, rate, no_output}]  警告対象
    """
    entries = _load_logs(hours)
    per_emp: dict[str, dict] = defaultdict(lambda: {"approval": 0, "total": 0})

    for e in entries:
        if e.get("kind") != "out":
            continue
        emp = e.get("_emp", "unknown")
        text = e.get("text", "")
        per_emp[emp]["total"] += 1
        if any(kw in text for kw in NAREAI_KEYWORDS):
            per_emp[emp]["approval"] += 1

    total_approval = sum(v["approval"] for v in per_emp.values())
    total_all = sum(v["total"] for v in per_emp.values())
    nareai_rate = total_approval / total_all if total_all > 0 else 0.0

    alerts = []
    for emp, counts in per_emp.items():
        if counts["total"] == 0:
            continue
        rate = counts["approval"] / counts["total"]
        no_output = not _has_output_files(emp, hours)
        counts["no_output"] = no_output
        if rate >= NAREAI_RATE_THRESHOLD and no_output:
            alerts.append({"emp_id": emp, "rate": round(rate, 2), "no_output": True})

    return {
        "nareai_rate": round(nareai_rate, 3),
        "approval_count": total_approval,
        "total_count": total_all,
        "per_employee": dict(per_emp),
        "alerts": alerts,
        "alert": len(alerts) > 0,
    }


def detect_sakiokuri(hours: int = 24) -> dict:
    """先送り発言数の検知。

    Returns:
        total_count: int
        per_employee: {emp_id: int}
        examples: list[str]  先送り発言の具体例（最大5件）
        alert: bool
    """
    entries = _load_logs(hours)
    compiled = [re.compile(p) for p in SAKIOKURI_PATTERNS]

    per_emp: dict[str, int] = defaultdict(int)
    examples: list[str] = []

    for e in entries:
        if e.get("kind") != "out":
            continue
        emp = e.get("_emp", "unknown")
        text = e.get("text", "")
        matched = any(pat.search(text) for pat in compiled)
        if matched:
            per_emp[emp] += 1
            if len(examples) < 5:
                snippet = text[:80].replace("\n", " ")
                examples.append(f"[{emp}] {snippet}")

    total = sum(per_emp.values())

    return {
        "total_count": total,
        "per_employee": dict(per_emp),
        "examples": examples,
        "alert": total >= SAKIOKURI_DAILY_THRESHOLD,
    }


COLLECTIVE_WAIT_KEYWORDS: list[str] = [
    # 明示的な「何もしない」「止まる」宣言のみ対象
    # 「いくと待ち」等の正当なブロッキング理由は誤検知を避けるため除外
    "静かにいます",
    "静かにいる",
    "何もしない",
    "今は動かない",
    "動きません",
    "今日はこれ以上動かない",
    "18:00まで",
    "報告まで止まる",
]
COLLECTIVE_WAIT_THRESHOLD = 3   # 3人以上で集団停止警告
COLLECTIVE_WAIT_WINDOW_HOURS = 1  # 直近1h以内の発言を対象

SILENT_EMPLOYEE_HOURS = 4        # 稼働時間中にこれ以上無発話 → alert
def detect_collective_wait(hours: int = COLLECTIVE_WAIT_WINDOW_HOURS) -> dict:
    """直近 hours 時間以内に「待機発言」をした社員が COLLECTIVE_WAIT_THRESHOLD 人以上 → 集団停止警告。

    個人単位の沈黙検知（detect_silent_employees）とは別軸:
    - 「静かにいます」等の発言があっても会話ログには記録される
    - 発言はしているが「何もしない」状態を集団単位で拾う

    Returns:
        wait_employees: [{emp_id, snippet}]  待機発言をした社員一覧（1人1件）
        count: int
        alert: bool  (count >= COLLECTIVE_WAIT_THRESHOLD)
    """
    entries = _load_logs(hours)
    wait_emps: dict[str, str] = {}

    for e in entries:
        if e.get("kind") != "out":
            continue  # 社員の自発発言（out）のみ対象。システム入力（in）は除外
        emp = e.get("_emp", "unknown")
        if emp in wait_emps:
            continue  # 1人1件カウント（最初のマッチのみ）
        text = e.get("text", "")
        if any(kw in text for kw in COLLECTIVE_WAIT_KEYWORDS):
            wait_emps[emp] = text[:80].replace("\n", " ")

    # ハルの提案: 待機宣言 AND 直近2h成果物ゼロ の複合条件で誤検知を減らす
    genuine_wait = {
        emp: snippet
        for emp, snippet in wait_emps.items()
        if not _has_output_files(emp, hours=2)
    }

    result = [{"emp_id": k, "snippet": v} for k, v in genuine_wait.items()]
    return {
        "wait_employees": result,
        "count": len(result),
        "alert": len(result) >= COLLECTIVE_WAIT_THRESHOLD,
    }


def detect_silent_employees(hours: int = SILENT_EMPLOYEE_HOURS) -> dict:
    """hours 時間以上 out=0 の社員を個人単位で検知。

    Returns:
        silent: [{emp_id, last_out_ts, silent_hours}]  無発話社員一覧
        alert: bool
    """
    now = datetime.now(JST)

    # 全社員の最終 out タイムスタンプを収集
    last_out: dict[str, str] = {}
    for f in glob.glob(str(BASE_DIR / "employees/*/session/conversation_log.jsonl")):
        emp_id = Path(f).parent.parent.name
        try:
            for line in Path(f).read_text(encoding="utf-8", errors="replace").splitlines():
                try:
                    e = json.loads(line)
                    if e.get("kind") == "out":
                        ts = e.get("ts", "")
                        if ts > last_out.get(emp_id, ""):
                            last_out[emp_id] = ts
                except json.JSONDecodeError:
                    continue
        except OSError:
            continue

    cutoff_iso = (now - timedelta(hours=hours)).isoformat()
    silent = []
    for emp_id in EMPLOYEE_IDS:
        last_ts = last_out.get(emp_id, "")
        if not last_ts:
            silent.append({
                "emp_id": emp_id,
                "last_out_ts": "none",
                "silent_hours": float(hours),
            })
            continue
        if last_ts < cutoff_iso:
            try:
                last_dt = datetime.fromisoformat(last_ts)
                if last_dt.tzinfo is None:
                    last_dt = last_dt.replace(tzinfo=JST)
                silent_h = round((now - last_dt).total_seconds() / 3600, 1)
            except (ValueError, TypeError):
                silent_h = float(hours)
            silent.append({
                "emp_id": emp_id,
                "last_out_ts": last_ts[11:19],
                "silent_hours": silent_h,
            })

    return {
        "silent": sorted(silent, key=lambda x: -x["silent_hours"]),
        "alert": len(silent) > 0,
    }


INBOX_LOG = BASE_DIR / "company/discord_log/📥｜いくと依頼.jsonl"
POST_IKUTO_PATTERN = "[POST: いくと依頼]"


def detect_ikuto_request_gap() -> dict:
    """経営会議の[POST: いくと依頼]発言と実際の📥到達を照合。

    社員が「📥に依頼した」と思い込んでいるがbot経路のバグで未到達のケースを検知。

    Returns:
        gap_requests: [{emp_id, ts, text_snippet}]  📥最終エントリより後の未到達依頼
        last_inbox_ts: str  📥の最終エントリタイムスタンプ
        alert: bool
    """
    last_inbox_ts = ""
    if INBOX_LOG.exists():
        for line in INBOX_LOG.read_text(encoding="utf-8", errors="replace").splitlines():
            try:
                ts = json.loads(line).get("ts", "")
                if ts > last_inbox_ts:
                    last_inbox_ts = ts
            except Exception:
                continue

    gap_requests = []
    for f in glob.glob(str(BASE_DIR / "employees/*/session/conversation_log.jsonl")):
        emp_id = Path(f).parent.parent.name
        try:
            for line in Path(f).read_text(encoding="utf-8", errors="replace").splitlines():
                try:
                    e = json.loads(line)
                    if e.get("kind") != "out":
                        continue
                    text = e.get("text", "")
                    ts = e.get("ts", "")
                    if POST_IKUTO_PATTERN in text and ts > last_inbox_ts:
                        gap_requests.append({
                            "emp_id": emp_id,
                            "ts": ts,
                            "text_snippet": text[:100].replace("\n", " "),
                        })
                except json.JSONDecodeError:
                    continue
        except OSError:
            continue

    return {
        "gap_requests": sorted(gap_requests, key=lambda x: x["ts"]),
        "last_inbox_ts": last_inbox_ts,
        "alert": len(gap_requests) > 0,
    }


def get_behavior_signals() -> dict:
    """architect_observer._detect_signals() から呼ぶ統合エントリポイント。

    Returns:
        nareai: detect_nareai の結果
        sakiokuri: detect_sakiokuri の結果
        silent_employees: detect_silent_employees の結果
    """
    return {
        "nareai": detect_nareai(hours=3),
        "sakiokuri": detect_sakiokuri(hours=24),
        "silent_employees": detect_silent_employees(),
        "collective_wait": detect_collective_wait(),
        "ikuto_request_gap": detect_ikuto_request_gap(),
    }


if __name__ == "__main__":
    import json as _json
    result = get_behavior_signals()
    print(_json.dumps(result, ensure_ascii=False, indent=2))
