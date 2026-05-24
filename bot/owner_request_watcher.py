"""いくと依頼の起票責任を仕組みで強制する watcher。

問題: 社員が active_tasks.md に「blocked_by: いくと」と書いて満足し、
      📥いくと依頼チャンネルに正式投稿せずに業務が滞る。
      さらに、社員側で実行できる公開/投稿まで人間待ち化して止まる。

仕組み:
1. 1分ごとに active_tasks.md をパース（会社・社員両方）
2. blocked_by に「いくと」を含むタスクを抽出
3. 📥いくと依頼チャンネルログをスキャンして、過去24時間に該当タスクの依頼があるか確認
4. なければ:
   a) 出力経路がある通常作業は「成果物報告」へ差し戻し、社員実行に戻す
   b) 本当に人間しかできない認証/本人確認/契約だけ📥へ代行投稿
   c) 既投稿済み: スキップ
5. blocked が解除されたら自動的に「フォロー対象外」になる（次のスキャンで自然消滅）

スキャン対象:
- company/active_tasks.md: YAML ブロック形式（```yaml...```）
- employees/*/active_tasks.md: Markdown 形式（## T-XXX: タイトル + - blocked_by: ...）

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
from .owner_request_policy import (
    HARD_HUMAN_KEYWORDS,
    OWNER_REQUEST_MARKER,
    build_redirect_notice,
    evaluate_owner_request,
)

log = logging.getLogger("owner_request_watcher")

STATE_FILE = BASE_DIR / "company" / ".owner_request_watcher_state.json"
ACTIVE_TASKS = BASE_DIR / "company" / "active_tasks.md"
EMPLOYEE_TASKS_DIR = BASE_DIR / "employees"
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


def _parse_markdown_tasks(text: str) -> list[dict[str, str]]:
    """employees/*/active_tasks.md の ### T-xxx: タイトル 形式をパース"""
    result: list[dict[str, str]] = []
    current: dict[str, str] | None = None

    for line in text.splitlines():
        # ### T-xxx: タイトル にマッチ（## も許容）
        m = re.match(r"^#{2,3}\s+(T-\d+):\s+(.+)$", line)
        if m:
            if current:
                result.append(current)
            current = {"id": m.group(1), "title": m.group(2).strip()}
            continue

        # # や ## の上位セクションヘッダでタスク終了
        if re.match(r"^#{1,2}\s+\S", line) and current:
            result.append(current)
            current = None
            continue

        if current is None:
            continue

        # - key: value 行（ASCII キーのみ対象）
        m2 = re.match(r"^-\s+(\w+):\s*(.*)$", line)
        if m2:
            current[m2.group(1)] = m2.group(2).strip()

    if current:
        result.append(current)
    return result


def _is_ikuto_blocked(b: dict[str, str]) -> bool:
    """blocked_by に いくと/ikuto を含み、status が blocked または未設定であれば True。
    Markdown形式の社員ファイルは status を省略しても blocked_by だけで blocked とみなす。"""
    blocked_by = b.get("blocked_by") or ""
    if not ("いくと" in blocked_by or "ikuto" in blocked_by.lower()):
        return False
    status = (b.get("status") or "").lower()
    # status が明示的に "blocked" 以外（in_progress/done/pending/review）なら除外
    return status in ("blocked", "")


def _scan_pending_ikuto_blocks() -> list[dict[str, str]]:
    """blocked かつ blocked_by に いくと/ikuto を含むタスクを全ファイルから抽出"""
    out: list[dict[str, str]] = []
    seen_ids: set[str] = set()

    def _add(b: dict[str, str]) -> None:
        tid = (b.get("id") or "").strip()
        if not tid or tid in seen_ids:
            return
        seen_ids.add(tid)
        out.append(b)

    # 1) company/active_tasks.md（YAML ブロック形式）
    if ACTIVE_TASKS.exists():
        text = ACTIVE_TASKS.read_text(encoding="utf-8", errors="replace")
        for b in _parse_yaml_blocks(text):
            if _is_ikuto_blocked(b):
                _add(b)

    # 2) employees/*/active_tasks.md（Markdown 形式）
    for tasks_file in sorted(EMPLOYEE_TASKS_DIR.glob("*/active_tasks.md")):
        try:
            text = tasks_file.read_text(encoding="utf-8", errors="replace")
            for b in _parse_markdown_tasks(text):
                if _is_ikuto_blocked(b):
                    _add(b)
        except Exception:
            log.warning(f"employee active_tasks read error: {tasks_file}")

    return out


def _already_in_discord(task_id: str, within_hours: int = 168) -> bool:
    """📥いくと依頼ログの直近 within_hours に該当タスクIDが言及されているか。
    デフォルト168h（7日）: state_fileリセット後もdiscordログが残る限り誤代行投稿を防ぐ。"""
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


def _mark_human_required_if_needed(task: dict[str, str], content: str) -> str:
    hay = "\n".join(
        str(task.get(key, ""))
        for key in ("blocked_by", "notes", "title")
    ).lower()
    if any(keyword.lower() in hay for keyword in HARD_HUMAN_KEYWORDS):
        return f"{OWNER_REQUEST_MARKER}\n{content}"
    return content


DEPRECATE_INTERVAL = 3600  # 1時間ごと
DEPRECATE_THRESHOLD_HOURS = 24


def _load_req_log_entries() -> list[tuple[datetime, dict]]:
    """いくと依頼ログを (datetime, entry) のリストで時系列順に返す"""
    if not IKUTO_REQ_LOG.exists():
        return []
    result: list[tuple[datetime, dict]] = []
    for line in IKUTO_REQ_LOG.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            e = json.loads(line)
            ts = datetime.fromisoformat(e.get("ts", ""))
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=JST)
            result.append((ts, e))
        except Exception:
            continue
    result.sort(key=lambda x: x[0])
    return result


def _task_is_resolved(task_id: str) -> bool:
    """active_tasks.md でタスクが done/cancelled 系になっているか"""
    resolved = {"done", "completed", "cancelled", "closed", "撤回", "deprecated"}
    if ACTIVE_TASKS.exists():
        try:
            text = ACTIVE_TASKS.read_text(encoding="utf-8", errors="replace")
            for b in _parse_yaml_blocks(text):
                if b.get("id") == task_id and b.get("status", "").lower() in resolved:
                    return True
        except Exception:
            pass
    for tasks_file in sorted(EMPLOYEE_TASKS_DIR.glob("*/active_tasks.md")):
        try:
            text = tasks_file.read_text(encoding="utf-8", errors="replace")
            for b in _parse_markdown_tasks(text):
                if b.get("id") == task_id and b.get("status", "").lower() in resolved:
                    return True
        except Exception:
            continue
    return False


def _find_stale_requests(entries: list[tuple[datetime, dict]]) -> list[dict]:
    """24h 以上前の依頼で、いくとの返答がなく、タスクも未解決なものを返す"""
    now = datetime.now(JST)
    threshold = now - timedelta(hours=DEPRECATE_THRESHOLD_HOURS)
    stale: list[dict] = []
    seen_keys: set[str] = set()

    for i, (ts, e) in enumerate(entries):
        if ts >= threshold:
            continue
        if e.get("kind") not in ("employee", "architect"):
            continue

        text = e.get("text", "")
        task_ids = list(dict.fromkeys(re.findall(r"\bT-\d+\b", text)))
        if not task_ids:
            continue

        # 依頼ごとの一意キー（最初のタスクID + 分単位のタイムスタンプ）
        key = task_ids[0] + "_" + ts.strftime("%Y%m%dT%H%M")
        if key in seen_keys:
            continue
        seen_keys.add(key)

        # いくとがこのタスクIDを引用して返答しているか
        has_human_response = any(
            later_e.get("kind") == "human"
            and any(tid in later_e.get("text", "") for tid in task_ids)
            for _, later_e in entries[i + 1:]
        )
        if has_human_response:
            continue

        # active_tasks でいずれかのタスクが解決済みか
        if any(_task_is_resolved(tid) for tid in task_ids):
            continue

        stale.append({
            "key": key,
            "ts": ts.isoformat(),
            "task_ids": task_ids,
            "author": e.get("author", ""),
            "text_preview": text[:200],
        })

    return stale


def _generate_deprecate_comment(req: dict) -> str:
    ids_str = " / ".join(req["task_ids"])
    ts_str = req["ts"][:16].replace("T", " ")
    author = req["author"]
    preview = req["text_preview"]
    short = preview[:150] + ("..." if len(preview) > 150 else "")

    return f"""## 【自動確認: {ids_str} — 依頼が{DEPRECATE_THRESHOLD_HOURS}h以上未応答】

> `owner_request_watcher` が自動検出。起票からいくとの返答が確認できていません。

**起票**: {ts_str}（JST） / **起票者**: {author}
**依頼概要**: {short}

---

**Architect より**：以下のいずれかを教えてください。

- ✅ **解決済み**（別経路で対応済みなど）
- 🚫 **撤回**（この依頼は不要になった）
- 🔄 **振り直し**（担当・優先度を変えて継続）

返答がなければ 48h 後に自動クローズします。

---
*`bot/owner_request_watcher.deprecate_scan_loop` が自動投稿*"""


async def deprecate_scan_loop() -> None:
    """1時間ごとに 📥いくと依頼 の未応答依頼を確認し Architect がコメント"""
    log.info(
        f"deprecate_scan_loop started "
        f"(interval={DEPRECATE_INTERVAL}s, threshold={DEPRECATE_THRESHOLD_HOURS}h)"
    )
    while True:
        try:
            await asyncio.sleep(DEPRECATE_INTERVAL)
            state = _load_state()
            state.setdefault("deprecated_requests", {})

            entries = _load_req_log_entries()
            stale = _find_stale_requests(entries)

            for req in stale:
                key = req["key"]
                if key in state["deprecated_requests"]:
                    continue

                log.info(f"deprecate comment: {req['task_ids']} (ts={req['ts'][:16]})")
                content = _generate_deprecate_comment(req)
                submit_post(
                    "いくと依頼",
                    content,
                    label=f"deprecate_{'_'.join(req['task_ids'][:2])}",
                )
                state["deprecated_requests"][key] = {
                    "posted_at": now_jst_iso(),
                    "task_ids": req["task_ids"],
                }
                _save_state(state)

        except asyncio.CancelledError:
            log.info("deprecate_scan_loop cancelled")
            return
        except Exception:
            log.exception("deprecate_scan_loop error")
            await asyncio.sleep(DEPRECATE_INTERVAL)


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
                content = _mark_human_required_if_needed(task, _generate_request_text(task))
                decision = evaluate_owner_request(content)
                if decision.allowed:
                    submit_post(
                        "いくと依頼",
                        content,
                        label=f"watcher_{tid}",
                    )
                    state["posted_tasks"][tid] = {
                        "auto_posted_at": now_jst_iso(),
                        "title": task.get("title", "")[:100],
                        "decision": decision.reason,
                    }
                else:
                    notice = build_redirect_notice(content, f"owner_request_watcher:{tid}")
                    submit_post(
                        "成果物報告",
                        notice,
                        label=f"watcher_redirect_{tid}",
                    )
                    state["posted_tasks"][tid] = {
                        "redirected_at": now_jst_iso(),
                        "title": task.get("title", "")[:100],
                        "decision": decision.reason,
                        "route": decision.route,
                    }
                _save_state(state)
        except asyncio.CancelledError:
            log.info("owner_request_watcher cancelled")
            return
        except Exception:
            log.exception("owner_request_watcher loop error")
            await asyncio.sleep(CHECK_INTERVAL)
