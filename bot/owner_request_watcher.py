"""いくと依頼の起票責任を仕組みで強制する watcher。

問題: 社員が active_tasks.md に「blocked_by: いくと」と書いて満足し、
      📥いくと依頼チャンネルに正式投稿せずに業務が滞る。

仕組み:
1. 1分ごとに active_tasks.md をパース
2. status: blocked かつ blocked_by に「いくと」を含むタスクを抽出
3. 📥いくと依頼チャンネルログをスキャンして、過去24時間に該当タスクの依頼があるか確認
4. なければ:
   a) 1回目: 状態ファイルに記録 + Architect が代行投稿（owner_request_protocol.md テンプレで自動生成）
   b) 既投稿済み: スキップ
5. blocked が解除されたら自動的に「フォロー対象外」になる（次のスキャンで自然消滅）

Claude/LLM を一切呼ばない（Python で完結）= トークン消費ゼロ。
"""
from __future__ import annotations

import asyncio
import json
import logging
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from .config import BASE_DIR, EMPLOYEES, JST, now_jst_iso
from .architect_outbox import submit_post

log = logging.getLogger("owner_request_watcher")

STATE_FILE = BASE_DIR / "company" / ".owner_request_watcher_state.json"
ACTIVE_TASKS = BASE_DIR / "company" / "active_tasks.md"
IKUTO_REQ_LOG = BASE_DIR / "company" / "discord_log" / "📥｜いくと依頼.jsonl"
CHECK_INTERVAL = 60  # 60秒ごとにスキャン


def _load_state() -> dict:
    if not STATE_FILE.exists():
        return {"posted_tasks": {}}
    try:
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {"posted_tasks": {}}


def _save_state(state: dict) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(
        json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def _parse_yaml_blocks(text: str) -> list[dict[str, str]]:
    """active_tasks.md から ```yaml ... ``` ブロックを抽出して簡易 key:value 化"""
    result: list[dict[str, str]] = []
    in_yaml = False
    current_lines: list[str] = []
    for line in text.splitlines():
        s = line.strip()
        if s.startswith("```yaml"):
            in_yaml = True
            current_lines = []
            continue
        if s == "```" and in_yaml:
            in_yaml = False
            kv: dict[str, str] = {}
            in_notes = False
            notes_lines: list[str] = []
            for ln in current_lines:
                if in_notes:
                    if ln.startswith("  ") or not ln.strip():
                        notes_lines.append(ln.strip())
                        continue
                    in_notes = False
                m = re.match(r"^([A-Za-z_][\w_]*):\s*(.*)$", ln)
                if m:
                    k, v = m.group(1), m.group(2).strip()
                    if k == "notes" and (v == "|" or v == ""):
                        in_notes = True
                        notes_lines = []
                        continue
                    kv[k] = v
            if notes_lines:
                kv["notes"] = "\n".join(l for l in notes_lines if l).strip()
            if kv:
                result.append(kv)
            continue
        if in_yaml:
            current_lines.append(line)
    return result


def _scan_pending_ikuto_blocks() -> list[dict[str, str]]:
    """blocked かつ blocked_by に いくと/ikuto を含むタスクを抽出"""
    if not ACTIVE_TASKS.exists():
        return []
    text = ACTIVE_TASKS.read_text(encoding="utf-8", errors="replace")
    blocks = _parse_yaml_blocks(text)
    out: list[dict[str, str]] = []
    for b in blocks:
        status = (b.get("status") or "").lower()
        blocked_by = (b.get("blocked_by") or "").lower()
        if status not in ("blocked",):
            continue
        if not blocked_by:
            continue
        if "いくと" in b.get("blocked_by", "") or "ikuto" in blocked_by:
            out.append(b)
    return out


def _already_in_discord(task_id: str, within_hours: int = 24) -> bool:
    """📥いくと依頼ログの直近 within_hours に該当タスクIDが言及されているか"""
    if not IKUTO_REQ_LOG.exists():
        return False
    cutoff = datetime.now(JST) - timedelta(hours=within_hours)
    for line in IKUTO_REQ_LOG.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            e = json.loads(line)
            ts_str = e.get("ts", "")
            ts = datetime.fromisoformat(ts_str)
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=JST)
            if ts < cutoff:
                continue
            if task_id and task_id in e.get("text", ""):
                return True
        except Exception:
            continue
    return False


def _normalize_owner_mention(owner: str) -> str:
    """yaml の owner 値を @表示名 に変換"""
    info = EMPLOYEES.get(owner.strip())
    if info:
        return f"@{info['display']}"
    return f"@{owner.strip()}"


def _generate_request_text(task: dict[str, str]) -> str:
    """active_tasks.md のタスクから owner_request_protocol.md テンプレで依頼文を自動生成"""
    tid = task.get("id", "T-?")
    title = task.get("title", "(タイトル不明)")
    blocked_by = task.get("blocked_by", "")
    notes = task.get("notes", "")
    due = task.get("due", "")
    priority = task.get("priority", "")
    owner_mention = _normalize_owner_mention(task.get("owner", ""))
    reviewer_mention = _normalize_owner_mention(task.get("reviewer", ""))

    return f"""## 【依頼: {tid} ブロッカー解除 — {title}】

> watcher 自動代行投稿。社員が`active_tasks.md`に「いくと待ち」と書いたが📥未投稿だったため、仕組みが代行しました。
> 起票責任は {owner_mention}（Owner）。今後は起票者が直接📥に正式投稿してください。

### なぜ必要か
タスク `{tid}` ({title}) が **status: blocked** で停止中。
ブロック原因: **{blocked_by}**

### 詳細手順（active_tasks.md の notes より自動抽出）
```
{notes if notes else '(notes 未記載 — 起票者は手順を追記してください)'}
```

### 期待される結果
- ブロッカー解除
- `{tid}` の作業再開
- 関連社員（Owner: {owner_mention}, Reviewer: {reviewer_mention}）が次のステップへ進める

### 完了時の報告先
{owner_mention} → 📥いくと依頼スレッドへ返信

### 緊急度
{priority if priority else '不明'} / 期限: {due if due else '未設定'}

### 起票者
{owner_mention}（active_tasks.md より自動取得）

---
*この依頼は `bot/owner_request_watcher.py` が active_tasks.md を監視して自動投稿したものです。起票者が手順を補完してください。*"""


async def scan_and_post_loop() -> None:
    """1分ごとに pending 依頼をチェック、未投稿なら代行投稿"""
    log.info(f"owner_request_watcher started (interval={CHECK_INTERVAL}s)")
    while True:
        try:
            await asyncio.sleep(CHECK_INTERVAL)
            state = _load_state()
            pending = _scan_pending_ikuto_blocks()
            for task in pending:
                tid = task.get("id", "").strip()
                if not tid or tid == "T-?":
                    continue
                if tid in state["posted_tasks"]:
                    continue  # 既投稿
                if _already_in_discord(tid):
                    state["posted_tasks"][tid] = {"detected_in_discord": now_jst_iso()}
                    _save_state(state)
                    continue
                # 代行投稿
                log.info(f"代行投稿: {tid} ({task.get('title','')[:60]})")
                content = _generate_request_text(task)
                submit_post(
                    "いくと依頼",
                    content,
                    label=f"watcher_{tid}",
                )
                state["posted_tasks"][tid] = {
                    "auto_posted_at": now_jst_iso(),
                    "title": task.get("title", "")[:100],
                }
                _save_state(state)
        except asyncio.CancelledError:
            log.info("owner_request_watcher cancelled")
            return
        except Exception:
            log.exception("owner_request_watcher loop error")
            await asyncio.sleep(CHECK_INTERVAL)
