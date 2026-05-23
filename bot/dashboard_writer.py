"""社員状態 dashboard を shared/dashboard.md に書き出す。

各社員の現状を1ファイルで一覧できるようにする。
- 直近1hでの out カウント
- 最終 out 時刻
- active タスク数（自分が owner）
- 過去24hの prompt_chars 合計（消費量）

15分ごとに更新。LLM 呼ばない。
"""
from __future__ import annotations

import asyncio
import glob
import json
import logging
import re
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path

from .config import BASE_DIR, EMPLOYEES, JST
from . import dynamic_config

log = logging.getLogger("dashboard_writer")

OUTPUT = BASE_DIR / "shared" / "dashboard.md"


def _employee_stats() -> list[dict]:
    now = datetime.now(JST)
    cutoff_1h = (now - timedelta(hours=1)).isoformat()
    cutoff_24h = (now - timedelta(hours=24)).isoformat()
    rows = []
    for emp_id, info in EMPLOYEES.items():
        log_path = BASE_DIR / "employees" / emp_id / "session" / "conversation_log.jsonl"
        out_1h = 0
        in_1h = 0
        last_out_ts = ""
        last_out_snippet = ""
        if log_path.exists():
            for line in log_path.read_text(encoding="utf-8", errors="replace").splitlines():
                try:
                    e = json.loads(line)
                except json.JSONDecodeError:
                    continue
                ts = e.get("ts", "")
                k = e.get("kind", "")
                if ts >= cutoff_1h:
                    if k == "out": out_1h += 1
                    if k == "in": in_1h += 1
                if k == "out":
                    last_out_ts = ts
                    last_out_snippet = e.get("text", "")[:80]
        # 過去24h prompt_chars
        prompt_24h = 0
        usage_path = BASE_DIR / "company" / "usage_metrics.jsonl"
        if usage_path.exists():
            for line in usage_path.read_text(encoding="utf-8", errors="replace").splitlines():
                try:
                    e = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if e.get("ts", "") < cutoff_24h:
                    continue
                if e.get("employee_id") != emp_id:
                    continue
                prompt_24h += int(e.get("prompt_chars") or 0)
        rows.append({
            "emp_id": emp_id,
            "display": info.get("display", emp_id),
            "role": info.get("role", ""),
            "out_1h": out_1h,
            "in_1h": in_1h,
            "last_out_ts": last_out_ts[11:19] if last_out_ts else "-",
            "last_out_snippet": last_out_snippet,
            "prompt_24h": prompt_24h,
        })
    return rows


def _task_stats_by_owner() -> dict[str, dict[str, int]]:
    path = BASE_DIR / "company" / "active_tasks.md"
    if not path.exists():
        return {}
    text = path.read_text(encoding="utf-8", errors="replace")
    by_owner: dict[str, Counter] = {}
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
            owner = re.search(r"owner:\s*(\S+)", bt)
            status = re.search(r"status:\s*(\S+)", bt)
            if owner and status:
                o = owner.group(1).strip()
                st = status.group(1).strip().lower()
                by_owner.setdefault(o, Counter())[st] += 1
            in_yaml = False
            block = []
            continue
        if in_yaml:
            block.append(line)
    return {k: dict(v) for k, v in by_owner.items()}


def render_dashboard() -> str:
    now = datetime.now(JST).strftime("%Y-%m-%d %H:%M JST")
    emp_rows = _employee_stats()
    task_by_owner = _task_stats_by_owner()

    lines = [
        "# AI NOWA 社員状態 Dashboard",
        "",
        f"自動生成: {now} （15分ごと更新）",
        "",
        "## 社員アクティビティ",
        "",
        "| 社員 | 役割 | out(1h) | in(1h) | 最終 out | prompt消費(24h) | 直近発話 |",
        "|------|------|---------|--------|----------|-----------------|----------|",
    ]
    for r in sorted(emp_rows, key=lambda x: -x["out_1h"]):
        snippet = r["last_out_snippet"].replace("|", "/").replace("\n", " ")[:50]
        lines.append(
            f"| {r['display']} | {r['role'][:12]} | {r['out_1h']} | {r['in_1h']} "
            f"| {r['last_out_ts']} | {r['prompt_24h']:,}字 | {snippet} |"
        )

    lines.extend(["", "## タスク owner 別", "", "| Owner | 合計 | done | in_progress | review | pending | blocked |", "|-------|------|------|-------------|--------|---------|---------|"])
    for owner, statuses in sorted(task_by_owner.items()):
        total = sum(statuses.values())
        lines.append(
            f"| {owner} | {total} | {statuses.get('done',0)} | {statuses.get('in_progress',0)} "
            f"| {statuses.get('review',0)} | {statuses.get('pending',0)} | {statuses.get('blocked',0)} |"
        )

    # 全体合計
    total_out_1h = sum(r["out_1h"] for r in emp_rows)
    total_prompt_24h = sum(r["prompt_24h"] for r in emp_rows)
    silent_emps = [r["display"] for r in emp_rows if r["out_1h"] == 0]
    lines.extend([
        "",
        "## サマリ",
        "",
        f"- 過去1時間の総 out: **{total_out_1h}** 件",
        f"- 過去24時間の総 prompt_chars: **{total_prompt_24h:,}** 字",
        f"- 過去1時間沈黙してた社員: {', '.join(silent_emps) if silent_emps else 'なし'}",
    ])

    # Section 3〜5: 自己改善ループ指標
    lines.extend(["", "---", ""])
    lines.extend(_render_improvement_sections())

    return "\n".join(lines) + "\n"


def _render_improvement_sections() -> list[str]:
    """自己改善ループの指標セクション（Section 3〜5）を生成する。"""
    state_file = BASE_DIR / "company" / ".self_improvement_state.json"
    ts_label = "--"
    cog: dict = {}
    rev: dict = {}
    eff: dict = {}
    qual: dict = {}
    trigger_history: list[dict] = []

    try:
        if state_file.exists():
            state = json.loads(state_file.read_text(encoding="utf-8"))
            snaps = state.get("snapshots", [])
            trigger_history = state.get("trigger_history", [])[-7:]
            if snaps:
                latest = snaps[-1]
                ts_label = latest.get("ts", "--")[:16].replace("T", " ")
                cog = latest.get("cognition", {})
                rev = latest.get("revenue", {})
                eff = latest.get("efficiency", {})
                qual = latest.get("quality", {})
                # 前回との差分
                if len(snaps) >= 2:
                    prev = snaps[-2].get("cognition", {})
                    cog["_d_stars"] = cog.get("stars", 0) - prev.get("stars", 0)
                    cog["_d_liked"] = cog.get("zenn_liked", 0) - prev.get("zenn_liked", 0)
                    cog["_d_hatena"] = cog.get("hatena_bookmarks", 0) - prev.get("hatena_bookmarks", 0)
    except Exception:
        pass

    def _sign(v: int) -> str:
        return f"+{v}" if v >= 0 else str(v)

    has_data = bool(eff)
    comp_rate = eff.get("completion_rate")
    comp_str = f"{comp_rate:.1%}" if comp_rate is not None else "--"
    comp_icon = ("🟢" if comp_rate >= 0.5 else "🔴") if comp_rate is not None else "--"
    postpone = qual.get("sakiokuri_count_24h") if qual else None
    postpone_str = str(postpone) if postpone is not None else "--"
    postpone_icon = ("🟢" if postpone < 5 else "🔴") if postpone is not None else "--"
    nareai = qual.get("nareai_rate") if qual else None
    nareai_str = f"{nareai:.1%}" if nareai is not None else "--"
    nareai_icon = ("🟢" if nareai < 0.6 else "🔴") if nareai is not None else "--"
    result_zero = len(qual.get("nareai_alerts", [])) if qual else None
    result_zero_str = str(result_zero) if result_zero is not None else "--"
    result_zero_icon = ("🟢" if result_zero == 0 else "🔴") if result_zero is not None else "--"
    gross = rev.get("gross_jpy")
    gross_str = f"¥{gross:,}" if gross is not None else "--"

    lines = [
        "## 認知・収益指標 [auto: 1h更新 / self_improvement_loop.py]",
        "",
        "| 指標 | 値 | 前回差分 | 更新時刻 |",
        "|------|----|---------|--------|",
        f"| GitHub stars | {cog.get('stars', '--')} | {_sign(cog.get('_d_stars', 0)) if cog else '--'} | {ts_label} |",
        f"| Zenn likes (全記事合計) | {cog.get('zenn_liked', '--')} | {_sign(cog.get('_d_liked', 0)) if cog else '--'} | {ts_label} |",
        f"| はてブ (全記事合計) | {cog.get('hatena_bookmarks', '--')} | {_sign(cog.get('_d_hatena', 0)) if cog else '--'} | {ts_label} |",
        f"| Design Kit v1 売上 | {gross_str} | -- | {ts_label} |",
        f"| Polar 注文数 | {rev.get('order_count', '--')} | -- | {ts_label} |",
        "",
        "## 効率・品質指標 [auto: 1h更新 / self_improvement_loop.py]",
        "",
        "| 指標 | 値 | 閾値 | 状態 |",
        "|------|---|-----|-----|",
        f"| 完了タスク数 | {eff.get('done_tasks', '--')} / {eff.get('total_tasks', '--')} | -- | -- |",
        f"| タスク完了率 | {comp_str} | > 50% | {comp_icon} |",
        f"| 先送り発言数 (24h) | {postpone_str} | < 5/日 | {postpone_icon} |",
        f"| 馴れ合い率 (3h) | {nareai_str} | < 60% | {nareai_icon} |",
        f"| 結果ゼロ社員 | {result_zero_str} | 0 | {result_zero_icon} |",
        "",
        "## 自動トリガー履歴 [過去7件 / self_improvement_loop.py]",
        "",
        "| 時刻 | トリガー | 詳細 |",
        "|-----|--------|------|",
    ]
    if trigger_history:
        for t in reversed(trigger_history):
            ts = t.get("ts", "--")[:16].replace("T", " ")
            lines.append(f"| {ts} | {t.get('trigger', '--')} | {t.get('detail', '--')[:60]} |")
    else:
        lines.append("| -- | -- | -- |")

    return lines


def write_dashboard() -> Path:
    content = render_dashboard()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(content, encoding="utf-8")
    return OUTPUT


async def dashboard_loop() -> None:
    interval = dynamic_config.get("dashboard_writer.interval_seconds", 900)
    log.info(f"dashboard_writer started (interval={interval}s = {interval//60}min)")
    while True:
        try:
            write_dashboard()
            interval = dynamic_config.get("dashboard_writer.interval_seconds", 900)
            await asyncio.sleep(interval)
        except asyncio.CancelledError:
            return
        except Exception:
            log.exception("dashboard_loop error")
            await asyncio.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    p = write_dashboard()
    print(f"written: {p}")
    print(p.read_text(encoding="utf-8")[:2500])
