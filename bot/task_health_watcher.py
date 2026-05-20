"""タスク健全性を機械的にチェックする watcher。

人間の会社に当たり前にある「業務管理」を最小実装で。
- 締切超過（due < today なのに status != done）
- 長期 in_progress（updated/created から72h 経過しても in_progress）
- deliverable 不在（status=done なのに deliverable ファイルがない）

LLM 呼ばない。Python のみ。1日1回 朝に📢で報告。
"""
from __future__ import annotations

import asyncio
import logging
import re
from datetime import datetime, timedelta
from pathlib import Path

from .config import BASE_DIR, JST
from . import dynamic_config

log = logging.getLogger("task_health_watcher")

ACTIVE_TASKS = BASE_DIR / "company" / "active_tasks.md"


def _parse_yaml_blocks(text: str) -> list[dict[str, str]]:
    result: list[dict[str, str]] = []
    in_yaml = False
    current: list[str] = []
    for line in text.splitlines():
        s = line.strip()
        if s.startswith("```yaml"):
            in_yaml = True
            current = []
            continue
        if s == "```" and in_yaml:
            in_yaml = False
            kv: dict[str, str] = {}
            for ln in current:
                m = re.match(r"^([A-Za-z_][\w_]*):\s*(.*)$", ln)
                if m:
                    kv[m.group(1)] = m.group(2).strip()
            if kv:
                result.append(kv)
            continue
        if in_yaml:
            current.append(line)
    return result


def _parse_date(s: str) -> datetime | None:
    """YAML 値から日付/日時を抽出"""
    s = (s or "").strip().strip('"').strip("'")
    if not s:
        return None
    for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M"):
        try:
            return datetime.strptime(s.split("+")[0].split("Z")[0], fmt).replace(tzinfo=JST)
        except ValueError:
            continue
    return None


def scan_task_health() -> dict:
    """active_tasks.md を読んで、3カテゴリの問題を抽出"""
    issues: dict = {
        "overdue": [],          # 締切超過
        "stale_in_progress": [],  # 長期 in_progress
        "missing_deliverable": [],  # deliverable 不在
    }
    if not ACTIVE_TASKS.exists():
        return issues
    text = ACTIVE_TASKS.read_text(encoding="utf-8", errors="replace")
    blocks = _parse_yaml_blocks(text)
    now = datetime.now(JST)
    stale_threshold_hours = dynamic_config.get("task_health.stale_threshold_hours", 24)
    stale_cutoff = now - timedelta(hours=stale_threshold_hours)

    for b in blocks:
        tid = (b.get("id") or "").strip()
        title = (b.get("title") or "").strip()
        status = (b.get("status") or "").strip().lower()
        due = _parse_date(b.get("due", ""))
        owner = (b.get("owner") or "").strip()
        deliverable = (b.get("deliverable") or "").strip()
        updated = _parse_date(b.get("updated") or b.get("created") or "")

        # 1. 締切超過
        if due and status not in ("done", "closed", "archived") and due < now:
            issues["overdue"].append({
                "id": tid, "title": title, "status": status,
                "owner": owner, "due": due.strftime("%Y-%m-%d"),
                "days_over": (now - due).days,
            })

        # 2. 長期 in_progress
        if status == "in_progress" and updated and updated < stale_cutoff:
            hours = int((now - updated).total_seconds() / 3600)
            issues["stale_in_progress"].append({
                "id": tid, "title": title, "owner": owner,
                "stale_hours": hours,
            })

        # 3. deliverable 不在
        if status == "done" and deliverable:
            path = BASE_DIR / deliverable
            if not path.exists():
                issues["missing_deliverable"].append({
                    "id": tid, "title": title, "owner": owner,
                    "deliverable": deliverable,
                })
    return issues


def format_report(issues: dict) -> str | None:
    """問題があればレポート生成。なければ None。"""
    parts = []
    if issues["overdue"]:
        parts.append("### 締切超過")
        for i in issues["overdue"][:10]:
            parts.append(f"- `{i['id']}` ({i['days_over']}日超過) — {i['title'][:50]} / owner: {i['owner']} / due: {i['due']}")
    if issues["stale_in_progress"]:
        parts.append("### 長期 in_progress（72h 以上動いていない）")
        for i in issues["stale_in_progress"][:10]:
            parts.append(f"- `{i['id']}` ({i['stale_hours']}h停滞) — {i['title'][:50]} / owner: {i['owner']}")
    if issues["missing_deliverable"]:
        parts.append("### 成果物不在（done だが deliverable ファイルなし）")
        for i in issues["missing_deliverable"][:10]:
            parts.append(f"- `{i['id']}` — {i['title'][:50]} / 期待: `{i['deliverable']}`")
    if not parts:
        return None
    return (
        "## タスク健全性レポート（Architect / 自動監視）\n\n"
        + "\n".join(parts)
        + "\n\nオーナーは確認・更新してください。整合性チェックは COO（@三枝ミオ）。"
    )


async def daily_scan_loop() -> None:
    """1日1回、朝に📢へ投稿。重複抑制のため state ファイルで記録。"""
    from .architect_outbox import submit_post
    STATE = BASE_DIR / "company" / ".task_health_state.json"
    import json
    while True:
        try:
            # 次の 9:00 JST まで待つ
            now = datetime.now(JST)
            target = now.replace(hour=9, minute=0, second=0, microsecond=0)
            if target <= now:
                target = target + timedelta(days=1)
            await asyncio.sleep((target - now).total_seconds())

            issues = scan_task_health()
            report = format_report(issues)
            if report:
                submit_post("お知らせ", report, label="task_health_report")
                log.info(f"task_health posted: overdue={len(issues['overdue'])}, stale={len(issues['stale_in_progress'])}, missing={len(issues['missing_deliverable'])}")
            else:
                log.info("task_health: 異常なし")
            STATE.write_text(json.dumps({"last_scan": datetime.now(JST).isoformat()}, ensure_ascii=False), encoding="utf-8")
        except asyncio.CancelledError:
            return
        except Exception:
            log.exception("task_health_watcher loop error")
            await asyncio.sleep(3600)


if __name__ == "__main__":
    # 単体テスト
    issues = scan_task_health()
    report = format_report(issues)
    print(report or "(異常なし)")
