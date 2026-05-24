"""Architect (Opus) が会社状態を継続観察する仕組み。

設計方針:
- Python の軽い「異常検知」で予備スクリーニング（LLM 呼ばない）
- 異常があれば Architect (Opus) を呼んで判断
- Architect の応答に介入指示があれば📢に投稿
- 1日4回まで（4時間ごと、9-21時、トークン消費を抑制）

異常検知シグナル:
1. 締切48h以内のタスクが status=in_progress 以下のまま
2. 過去3時間で同一キーワードが30回以上出現（ループ議論）
3. 過去2時間で全社員の out が合計0件（議論停止）
4. 直近1時間の prompt_chars が 60000字超（過熱）
"""
from __future__ import annotations

import asyncio
import json
import logging
import re
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path

from .config import BASE_DIR, JST, now_jst_iso
from . import dynamic_config

log = logging.getLogger("architect_observer")

ACTIVE_TASKS = BASE_DIR / "company" / "active_tasks.md"
STATE_FILE = BASE_DIR / "company" / ".architect_observer_state.json"

SILENT_HOUR_START = 23
SILENT_HOUR_END = 7


def _is_silent_hour() -> bool:
    # 2026-05-23 いくと禁止令: AI に人間スケジュール持ち込み NG。Architect observer も 24h 稼働。
    return False


def _detect_signals() -> dict:
    """Python のみで会社状態の異常をスクリーニング。"""
    signals: dict = {
        "tight_deadlines": [],
        "loop_topics": [],
        "silent_company": False,
        "token_overheat": None,
        "nareai": None,
        "sakiokuri": None,
        "code_health": None,
        "silent_employees": None,
    }
    now = datetime.now(JST)

    # 1. 期限超過または締切48h以内 + in_progress 以下
    if ACTIVE_TASKS.exists():
        text = ACTIVE_TASKS.read_text(encoding="utf-8", errors="replace")
        in_yaml = False
        block: list[str] = []
        for line in text.splitlines():
            s = line.strip()
            if s.startswith("```yaml"):
                in_yaml = True
                block = []
                continue
            if s == "```" and in_yaml:
                bt = "\n".join(block)
                stat = re.search(r"status:\s*(\S+)", bt)
                due = re.search(r"due:\s*(\S+)", bt)
                tid = re.search(r"id:\s*(\S+)", bt)
                title = re.search(r"title:\s*(.+)", bt)
                own = re.search(r"owner:\s*(\S+)", bt)
                if stat and due and tid:
                    st = stat.group(1).lower()
                    if st in ("in_progress", "pending", "review"):
                        try:
                            d = datetime.strptime(due.group(1), "%Y-%m-%d").replace(tzinfo=JST)
                            hours_left = (d - now).total_seconds() / 3600
                            if hours_left < 48:
                                signals["tight_deadlines"].append({
                                    "id": tid.group(1),
                                    "title": (title.group(1) if title else "")[:50],
                                    "owner": own.group(1) if own else "?",
                                    "status": st,
                                    "hours_left": int(hours_left),
                                    "overdue": hours_left <= 0,
                                })
                        except ValueError:
                            pass
                in_yaml = False
                block = []
                continue
            if in_yaml:
                block.append(line)

    # 2. ループトピック検出（過去3時間）
    watched_keywords = dynamic_config.get("architect_observer.watched_keywords", [
        "AdSense", "Public", "Private", "公開判断", "監査", "法務", "ブロッカー", "撤退", "Zenn", "404",
    ])
    keyword_loop_threshold = dynamic_config.get("architect_observer.keyword_loop_threshold", 30)
    cutoff_3h = (now - timedelta(hours=3)).isoformat()
    counter: Counter = Counter()
    import glob
    for f in glob.glob(str(BASE_DIR / "employees/*/session/conversation_log.jsonl")):
        try:
            for line in Path(f).read_text(encoding="utf-8", errors="replace").splitlines():
                e = json.loads(line)
                if e.get("ts", "") < cutoff_3h:
                    continue
                t = e.get("text", "")
                for kw in watched_keywords:
                    if kw in t:
                        counter[kw] += 1
        except Exception:
            continue
    for kw, c in counter.most_common():
        if c >= keyword_loop_threshold:
            signals["loop_topics"].append({"keyword": kw, "count": c})

    # 3. 沈黙の会社（過去 silent_hours 時間、out 合計0件）
    silent_hours = dynamic_config.get("architect_observer.silent_hours", 2)
    cutoff_silent = (now - timedelta(hours=silent_hours)).isoformat()
    out_total = 0
    for f in glob.glob(str(BASE_DIR / "employees/*/session/conversation_log.jsonl")):
        try:
            for line in Path(f).read_text(encoding="utf-8", errors="replace").splitlines():
                e = json.loads(line)
                if e.get("ts", "") < cutoff_silent:
                    continue
                if e.get("kind") == "out":
                    out_total += 1
        except Exception:
            continue
    if out_total == 0:
        signals["silent_company"] = True

    # 4. トークン過熱（直近1時間）
    token_overheat_threshold = dynamic_config.get("architect_observer.token_overheat_threshold", 60000)
    try:
        from .context_assembler import check_recent_token_pace
        pace = check_recent_token_pace(window_minutes=60)
        if pace["prompt_chars"] > token_overheat_threshold:
            signals["token_overheat"] = {
                "prompt_chars": pace["prompt_chars"],
                "top": pace["top_employee"],
            }
    except Exception:
        log.exception("token pace check failed")

    # 5. 馴れ合い率 + 先送り発言数 + 沈黙社員（個人単位）
    try:
        from .behavior_metrics import get_behavior_signals
        bsig = get_behavior_signals()
        if bsig["nareai"]["alert"]:
            signals["nareai"] = bsig["nareai"]
        if bsig["sakiokuri"]["alert"]:
            signals["sakiokuri"] = bsig["sakiokuri"]
        se = bsig.get("silent_employees", {})
        if se.get("alert"):
            signals["silent_employees"] = se
    except Exception:
        log.exception("behavior metrics check failed")

    # 6. コードベース異常検知（例外頻発・再起動ループ・未クローズ incidents）
    try:
        from .code_health_monitor import get_code_health_signals
        csig = get_code_health_signals()
        if csig["any_alert"]:
            signals["code_health"] = csig
    except Exception:
        log.exception("code health check failed")

    return signals


def _has_anomaly(signals: dict) -> bool:
    return bool(
        signals["tight_deadlines"]
        or signals["loop_topics"]
        or signals["silent_company"]
        or signals["token_overheat"]
        or signals.get("nareai")
        or signals.get("sakiokuri")
        or signals.get("code_health")
        or signals.get("silent_employees")
    )


def _summarize_for_architect(signals: dict) -> str:
    parts = ["[observer より] 会社状態の異常スクリーニング結果:\n"]
    if signals["tight_deadlines"]:
        parts.append("## 期限超過または締切48h以内")
        for x in signals["tight_deadlines"][:8]:
            due_state = f"{abs(x['hours_left'])}h超過" if x.get("overdue") else f"{x['hours_left']}h残"
            parts.append(f"- {x['id']} ({due_state}) owner={x['owner']} status={x['status']} — {x['title']}")
    if signals["loop_topics"]:
        parts.append("\n## ループ疑い（過去3hで30回以上出現）")
        for x in signals["loop_topics"]:
            parts.append(f"- {x['keyword']}: {x['count']}回")
    if signals["silent_company"]:
        silent_hours = dynamic_config.get("architect_observer.silent_hours", 2)
        parts.append(f"\n## 沈黙: 過去 {silent_hours}h で全社員 out=0 件")
    if signals["token_overheat"]:
        ot = signals["token_overheat"]
        top = ot["top"]
        parts.append(f"\n## トークン過熱: 1h で {ot['prompt_chars']:,}字 (top={top[0] if top else '?'}: {top[1] if top else 0:,}字)")
    if signals.get("code_health"):
        ch = signals["code_health"]
        parts.append("\n## コードベース異常")
        error_modules = ch.get("error_modules", {})
        restart_loop = ch.get("restart_loop", {})
        open_incidents = ch.get("open_incidents", {})
        if error_modules.get("alert"):
            for a in error_modules.get("alerts", [])[:5]:
                parts.append(f"  - [{a['module']}] ERROR×{a['error']} CRITICAL×{a['critical']} (過去1h)")
        if restart_loop.get("alert"):
            parts.append(f"  - dispatcher 再起動 {restart_loop.get('restart_count', 0)}回 (過去1h)")
        if open_incidents.get("alert"):
            for inc in open_incidents.get("open_incidents", [])[:3]:
                parts.append(f"  - [{inc['ts']}] {inc['severity']}: {inc['kind']} — {inc['detail']}")
    if signals.get("nareai"):
        nr = signals["nareai"]
        parts.append(f"\n## 馴れ合い警告: 過去3h 承認発言率 {nr['nareai_rate']:.0%} ({nr['approval_count']}/{nr['total_count']}件)")
        for a in nr.get("alerts", [])[:5]:
            parts.append(f"  - {a['emp_id']}: 承認率 {a['rate']:.0%}、成果物ゼロ")
    if signals.get("sakiokuri"):
        sk = signals["sakiokuri"]
        parts.append(f"\n## 先送り警告: 過去24h 先送り発言 {sk['total_count']}件")
        for emp, cnt in sorted(sk["per_employee"].items(), key=lambda x: -x[1])[:5]:
            parts.append(f"  - {emp}: {cnt}件")
        for ex in sk.get("examples", [])[:3]:
            parts.append(f"  例: {ex}")
    if signals.get("silent_employees"):
        se = signals["silent_employees"]
        parts.append(f"\n## 沈黙社員（個人単位・稼働時間中）")
        for emp in se["silent"][:9]:
            parts.append(f"  - {emp['emp_id']}: {emp['silent_hours']}h 無発話 (最終: {emp['last_out_ts']})")
    parts.append(
        "\n\n設計者（Opus）として判断してください。今介入すべきか / すべきなら何を伝えるか。"
        "\n介入する場合: 応答内に `[INTERVENE]<介入文>[/INTERVENE]` を含める（介入文は📢お知らせに投稿される）。"
        "\n介入しない場合: 「異常なし」のみ短く返す。"
        "\n\n注意: 介入は短く、具体的に。社員の判断領域を侵さず、見落としを差し戻す形式で。"
    )
    return "\n".join(parts)


_INTERVENE_RE = re.compile(r"\[INTERVENE\](.+?)\[/INTERVENE\]", re.DOTALL | re.IGNORECASE)


def _extract_intervention(response: str) -> str | None:
    m = _INTERVENE_RE.search(response)
    if not m:
        return None
    text = m.group(1).strip()
    return text if len(text) >= 20 else None


async def observe_once() -> None:
    """1回の観察サイクル。"""
    signals = _detect_signals()
    if not _has_anomaly(signals):
        log.info("architect_observer: 異常なし (skip LLM)")
        return

    # 異常検出 → Architect (Opus) 呼び出し
    log.info(f"architect_observer: 異常検出、Architect 呼び出し: {signals}")
    from .architect import run_architect
    summary = _summarize_for_architect(signals)
    try:
        response = await run_architect(
            summary,
            sender="observer",
            channel="auto",
            mode="observer",
            use_resume=False,
        )
    except Exception:
        log.exception("run_architect failed in observer")
        return

    intervention = _extract_intervention(response)
    if not intervention:
        log.info("architect_observer: 介入なし判定")
        return

    # 介入投稿
    from .architect_outbox import submit_post
    submit_post(
        "お知らせ",
        f"## Architect 自律観察介入\n\n{intervention}\n\n---\n*自動観察 (4時間ごと) による介入です。*",
        label="observer_intervention",
    )
    log.info(f"architect_observer: 介入投稿 ({len(intervention)}字)")

    # state 記録
    try:
        state = json.loads(STATE_FILE.read_text(encoding="utf-8")) if STATE_FILE.exists() else {}
    except Exception:
        state = {}
    state.setdefault("interventions", []).append({
        "ts": now_jst_iso(),
        "signals": signals,
        "intervention_chars": len(intervention),
    })
    STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


async def observer_loop() -> None:
    interval = dynamic_config.get("architect_observer.check_interval_seconds", 12600)
    log.info(f"architect_observer started (interval={interval}s = {interval//3600}h)")
    # 初回は起動後30分置いてから（dispatcher 立ち上がりの混乱を回避）
    await asyncio.sleep(dynamic_config.get("architect_observer.initial_delay_seconds", 1800))
    while True:
        try:
            interval = dynamic_config.get("architect_observer.check_interval_seconds", 12600)
            if _is_silent_hour():
                await asyncio.sleep(interval)
                continue
            await observe_once()
            await asyncio.sleep(interval)
        except asyncio.CancelledError:
            return
        except Exception:
            log.exception("observer_loop error")
            await asyncio.sleep(interval)


if __name__ == "__main__":
    # 単体テスト
    signals = _detect_signals()
    print(json.dumps(signals, ensure_ascii=False, indent=2))
    print()
    print("anomaly:", _has_anomaly(signals))
    if _has_anomaly(signals):
        print()
        print(_summarize_for_architect(signals))
