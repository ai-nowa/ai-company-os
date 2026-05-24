"""Token-light context assembly and usage metrics.

The goal is not to make employees less autonomous. It is to give them the
same kind of prepared desk brief a human employee would use before deciding
whether to speak, work, or wait.
"""
from __future__ import annotations

import json
import re
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional

from .config import BASE_DIR, COMPANY_DIR, EMPLOYEES, JST, now_jst_iso
from .activity_index import last_employee_out_ts

MAX_DIGEST_CHARS = 4000
USAGE_METRICS_PATH = COMPANY_DIR / "usage_metrics.jsonl"
USAGE_REPORT_PATH = COMPANY_DIR / "usage_report.md"
COORDINATOR_EMPLOYEES = {"arima_reiji", "saegusa_mio", "asakura_noa"}
USAGE_METRICS_MAX_BYTES = 2_000_000
USAGE_METRICS_RETENTION_HOURS = 72
USAGE_METRICS_MAX_LINES = 20_000


def _read_jsonl(path: Path, limit: int = 200) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()[-limit:]
    events: list[dict[str, Any]] = []
    for line in lines:
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return events


def _short(text: str, limit: int) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) <= limit:
        return text
    return text[: max(0, limit - 1)].rstrip() + "…"


def _display_tokens(employee_id: str) -> set[str]:
    info = EMPLOYEES.get(employee_id, {})
    display = info.get("display", "")
    tokens = {employee_id}
    if display:
        tokens.add(display)
        m = re.match(r"^([一-鿿々ヶ]+)(.+)$", display)
        if m:
            tokens.add(m.group(1))
            tokens.add(m.group(2))
    return {t for t in tokens if t}


def _text_mentions_employee(text: str, employee_id: str) -> bool:
    return any(f"@{token}" in text or token in text for token in _display_tokens(employee_id))


def _recent_discord_events(limit_per_file: int = 40) -> list[dict[str, Any]]:
    log_dir = COMPANY_DIR / "discord_log"
    if not log_dir.exists():
        return []
    events: list[dict[str, Any]] = []
    for path in log_dir.glob("*.jsonl"):
        for event in _read_jsonl(path, limit=limit_per_file):
            event = dict(event)
            event["_channel"] = path.stem
            events.append(event)
    events.sort(key=lambda e: e.get("ts", ""))
    return events


def _last_own_out_ts(employee_id: str) -> str:
    """この社員自身が最後に投稿した out の ts（応答済みかどうかの判定に使う）"""
    return last_employee_out_ts(employee_id)


def _recent_mentions(employee_id: str, max_items: int = 5) -> list[str]:
    """自分の最終 out **以降** に来たメンションだけ返す。

    これがないと autonomy tick のたびに過去の解決済みメンション（例: いくとの古い発言）
    を「未対応」として再応答してしまい、「それはもう解決してますよー」が繰り返される。
    """
    last_out = _last_own_out_ts(employee_id)
    items: list[tuple[str, str]] = []
    inbox_path = BASE_DIR / "employees" / employee_id / "inbox" / "mentions.jsonl"
    for event in _read_jsonl(inbox_path, limit=100):
        ts = str(event.get("ts", ""))
        if last_out and ts <= last_out:
            continue
        sender = event.get("sender", "?")
        channel = event.get("channel", "?")
        reason = event.get("deferred_reason", "deferred")
        text = str(event.get("text", ""))
        items.append((ts, f"- {ts} #{channel} {sender} ({reason}): {_short(text, 220)}"))

    for event in reversed(_recent_discord_events()):
        ts = str(event.get("ts", ""))
        # 自分が最後に発言した時刻より新しいメンションだけ拾う
        if last_out and ts <= last_out:
            continue
        text = str(event.get("text", ""))
        if not _text_mentions_employee(text, employee_id):
            continue
        channel = event.get("_channel", "?")
        author = event.get("author", event.get("from", "?"))
        items.append((ts, f"- {ts} #{channel} {author}: {_short(text, 220)}"))
        if len(items) >= max_items * 2:
            break
    items.sort(key=lambda x: x[0])
    return [item for _, item in items[-max_items:]]


def _active_task_items(employee_id: str, max_items: int = 5) -> list[str]:
    """active_tasks.md から「動けるタスクだけ」を抽出。
    blocked / done のタスクは仕組み上 context に流さない（無駄会話の根本対策）。
    解除されたら自動で復活する（次回呼び出し時に再評価）。
    """
    path = COMPANY_DIR / "active_tasks.md"
    if not path.exists():
        return []
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    tokens = _display_tokens(employee_id)

    # yaml ブロックに分割
    blocks: list[list[str]] = []
    current: list[str] = []
    in_yaml = False
    in_current_tasks = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("## 現在のタスク"):
            in_current_tasks = True
        if stripped.startswith("```yaml"):
            if in_current_tasks:
                in_yaml = True
                current = []
            continue
        if stripped == "```" and in_yaml:
            in_yaml = False
            if current:
                blocks.append(current)
            current = []
            continue
        if in_yaml:
            current.append(line)

    items: list[str] = []
    for block in blocks:
        block_text = "\n".join(block)
        block_lower = block_text.lower()
        role_lines: list[str] = []
        for ln in block:
            s = ln.strip()
            if s.startswith(("owner:", "reviewer:", "buddy:", "audit:", "assignee:")):
                role_lines.append(s.split(":", 1)[1].split("#", 1)[0].strip())
        role_text = " ".join(role_lines).lower()
        # 自分が明示的に関係しているか（notes本文の名前は拾わない）
        if not role_text or not any(t.lower() in role_text for t in tokens):
            continue
        # 動けないステータスは除外（blocked / done / closed / archived）
        if "status: blocked" in block_lower or "status: done" in block_lower:
            continue
        if "status: closed" in block_lower or "status: archived" in block_lower:
            continue
        # 1行サマリ（id, title, status, due, next_action_now）を抽出
        summary_parts = []
        has_next_action = False
        for ln in block:
            s = ln.strip()
            if s.startswith(("id:", "title:", "status:", "due:", "priority:", "next_action_now:")):
                summary_parts.append(s)
                if s.startswith("next_action_now:"):
                    has_next_action = True
            if len(summary_parts) >= 6:
                break
        if summary_parts:
            if not has_next_action and any(part.startswith("due:") for part in summary_parts):
                summary_parts.append("next_action_now: due前に今できる準備・草稿・検証を進める")
            items.append("- " + _short(" / ".join(summary_parts), 260))
            if len(items) >= max_items:
                break
    return items


def _related_recent_logs(employee_id: str, max_items: int = 10, *, after_last_out: bool = False) -> list[str]:
    defaults = set(EMPLOYEES.get(employee_id, {}).get("default_channels", []))
    all_visible = "all" in defaults
    last_out = _last_own_out_ts(employee_id) if after_last_out else ""
    items: list[str] = []
    for event in reversed(_recent_discord_events()):
        ts = str(event.get("ts", ""))
        if last_out and ts <= last_out:
            continue
        channel = str(event.get("_channel", ""))
        text = str(event.get("text", ""))
        channel_match = all_visible or any(needle and needle in channel for needle in defaults)
        if not channel_match and not _text_mentions_employee(text, employee_id):
            continue
        author = event.get("author", event.get("from", "?"))
        items.append(f"- {event.get('ts', '')} #{channel} {author}: {_short(text, 180)}")
        if len(items) >= max_items:
            break
    return list(reversed(items))


def _new_artifacts(employee_id: str, max_items: int = 5) -> list[str]:
    roots = [
        BASE_DIR / "shared" / "docs",
        BASE_DIR / "shared" / "articles",
        BASE_DIR / "articles",
    ]
    if employee_id in COORDINATOR_EMPLOYEES:
        for emp_id in EMPLOYEES:
            roots.append(BASE_DIR / "employees" / emp_id / "outbox")
    else:
        roots.append(BASE_DIR / "employees" / employee_id / "outbox")

    files: list[Path] = []
    cutoff = datetime.now(JST) - timedelta(days=2)
    for root in roots:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if not path.is_file():
                continue
            if any(part in {"_archive", "archive"} for part in path.parts):
                continue
            try:
                mtime = datetime.fromtimestamp(path.stat().st_mtime, JST)
            except OSError:
                continue
            if mtime >= cutoff:
                files.append(path)
    files.sort(key=lambda p: p.stat().st_mtime if p.exists() else 0, reverse=True)
    items: list[str] = []
    for path in files[:max_items]:
        try:
            rel = path.relative_to(BASE_DIR)
        except ValueError:
            rel = path
        items.append(f"- {rel}")
    return items


def _continuity_snippets(employee_id: str, mode: str) -> list[str]:
    """社員の継続性を保つための短い記憶。

    Claude Code の full resume を毎回使わなくても、社員が「昨日までの自分」
    として話せる最低限だけを state_digest に入れる。
    """
    if mode == "micro":
        budget = 500
    elif mode == "routine":
        budget = 1000
    else:
        budget = 1500

    home = BASE_DIR / "employees" / employee_id
    parts: list[str] = []

    state_path = home / "session" / "session_state.json"
    try:
        state = json.loads(state_path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        state = {}
    last_summary = str(state.get("last_summary") or "").strip()
    if last_summary:
        parts.append(f"- last_summary: {_short(last_summary, 280)}")

    recent_context = (home / "session" / "recent_context.md").read_text(
        encoding="utf-8", errors="replace"
    ) if (home / "session" / "recent_context.md").exists() else ""
    if recent_context.strip():
        parts.append(f"- recent_context: {_short(recent_context, 420)}")

    for name in ("decisions", "learnings", "facts"):
        path = home / "memory" / f"{name}.md"
        if not path.exists():
            continue
        content = path.read_text(encoding="utf-8", errors="replace").strip()
        if not content or "（運用開始後にここに蓄積されます）" in content:
            continue
        parts.append(f"- memory/{name}: {_short(content, 360)}")

    result: list[str] = []
    used = 0
    for part in parts:
        if used + len(part) > budget:
            remaining = max(0, budget - used)
            if remaining > 80:
                result.append(_short(part, remaining))
            break
        result.append(part)
        used += len(part)
    return result


_WISDOM_CACHE: dict[str, tuple[float, str]] = {}


def _load_wisdom_essence() -> str:
    """shared/wisdom/_essence.md を読み込んで state_digest に注入する用に整形。
    キャッシュで毎回ファイル I/O しない（5 分 TTL）。"""
    import time
    path = BASE_DIR / "shared" / "wisdom" / "_essence.md"
    now = time.time()
    cached = _WISDOM_CACHE.get(str(path))
    if cached and now - cached[0] < 300:
        return cached[1]
    if not path.exists():
        return ""
    try:
        text = path.read_text(encoding="utf-8")
        # 「全社員必読エッセンス」見出しは省略、本文だけ
        lines = text.strip().split("\n")
        # 最初の H1 を除く
        if lines and lines[0].startswith("# "):
            lines = lines[1:]
        body = "\n".join(lines).strip()
        _WISDOM_CACHE[str(path)] = (now, body)
        return body
    except Exception:
        return ""


_DIGEST_BUDGETS = {
    "micro": {
        "release": 520,
        "routes": 0,
        "revenue": 560,
        "external_kpi": 520,
        "mentions": 620,
        "tasks": 620,
        "logs": 520,
        "artifacts": 220,
        "continuity": 360,
        "wisdom": 260,
    },
    "routine": {
        "release": 640,
        "routes": 740,
        "revenue": 700,
        "external_kpi": 620,
        "mentions": 700,
        "tasks": 720,
        "logs": 720,
        "artifacts": 260,
        "continuity": 500,
        "wisdom": 320,
    },
    "work": {
        "release": 760,
        "routes": 900,
        "revenue": 820,
        "external_kpi": 760,
        "mentions": 760,
        "tasks": 820,
        "logs": 860,
        "artifacts": 320,
        "continuity": 640,
        "wisdom": 360,
    },
    "executive": {
        "release": 820,
        "routes": 900,
        "revenue": 900,
        "external_kpi": 820,
        "mentions": 820,
        "tasks": 860,
        "logs": 820,
        "artifacts": 340,
        "continuity": 620,
        "wisdom": 380,
    },
}


def _fit_section(title: str, items: list[str], budget: int, fallback: str) -> list[str]:
    """Make a section that never steals budget from later high-value sections."""
    lines = [f"## {title}"]
    raw_items = items or [fallback]
    used = 0
    for raw in raw_items:
        for part in str(raw).splitlines():
            part = part.strip()
            if not part:
                continue
            remaining = budget - used
            if remaining <= 0:
                return lines + ["- ..."]
            clipped = _short(part, min(remaining, 240))
            lines.append(clipped)
            used += len(clipped) + 1
    return lines


def _wisdom_items(limit: int) -> list[str]:
    text = _load_wisdom_essence()
    if not text:
        return []
    items: list[str] = []
    used = 0
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if not line.startswith("-"):
            line = f"- {line}"
        if used + len(line) > limit:
            remaining = limit - used
            if remaining > 80:
                items.append(_short(line, remaining))
            break
        items.append(line)
        used += len(line) + 1
    return items


def _revenue_ops_items(employee_id: str, mode: str, limit: int) -> list[str]:
    try:
        from .revenue_ops import revenue_digest

        text = revenue_digest(max_chars=limit, employee_id=employee_id)
    except Exception:
        return []
    if not text.strip():
        return []
    return [line for line in text.splitlines() if line.strip()]


def _release_items(employee_id: str, limit: int) -> list[str]:
    try:
        from .release_board import release_digest

        text = release_digest(max_chars=limit, employee_id=employee_id)
    except Exception:
        return []
    if not text.strip():
        return []
    return [line for line in text.splitlines() if line.strip()]


def _external_kpi_items(limit: int) -> list[str]:
    try:
        from .external_metrics import external_digest_items

        items = external_digest_items(max_items=8)
    except Exception:
        return []
    result: list[str] = []
    used = 0
    for item in items:
        if used + len(item) > limit:
            remaining = limit - used
            if remaining > 80:
                result.append(_short(item, remaining))
            break
        result.append(item)
        used += len(item) + 1
    return result


def _output_route_items(mode: str, limit: int) -> list[str]:
    if mode == "micro":
        return []
    try:
        from .output_routes import output_route_items

        return output_route_items(max_chars=limit)
    except Exception:
        return []


def assemble_state_digest(employee_id: str, reason: str, mode: str = "routine") -> str:
    """Build a compact dynamic context digest for an employee call."""
    info = EMPLOYEES.get(employee_id, {})
    budgets = _DIGEST_BUDGETS.get(mode, _DIGEST_BUDGETS["routine"])
    sections = [
        "# state_digest",
        f"- employee: {info.get('display', employee_id)} ({info.get('role', '')})",
        f"- mode: {mode}",
        f"- reason: {_short(reason, 360)}",
        "",
        "## 期限の読み方（待機禁止）",
        "- due/期限/判定日/観察日は待機日ではなく最遅締切。未来日でも今できる準備・草稿・検証を進める",
        "- 待つ必要がある時だけ blocked_by を明記し、同時に next_action_now または別タスクを進める",
        "- 投稿/公開/確認をいくとへ依頼しない。Output Routesのどれかへ出すか、失敗理由と代替公開パスを成果物報告へ残す",
        "",
        *_fit_section("Release OS（公開・出荷ゲート）", _release_items(employee_id, budgets["release"]), budgets["release"], "- 未初期化"),
        "",
        *([] if mode == "micro" else _fit_section("Output Routes（人間待ち禁止・先に試す出口）", _output_route_items(mode, budgets.get("routes", 0)), budgets.get("routes", 0), "- 未定義")),
        *([] if mode == "micro" else [""]),
        *_fit_section("Revenue OS（収益ループ）", _revenue_ops_items(employee_id, mode, budgets["revenue"]), budgets["revenue"], "- 未初期化"),
        "",
        *_fit_section("外部KPI実測（自動取得・未取得は0ではない）", _external_kpi_items(budgets["external_kpi"]), budgets["external_kpi"], "- スナップショットなし"),
        "",
        *_fit_section("自分宛メンション（最大5件）", _recent_mentions(employee_id), budgets["mentions"], "- なし"),
        "",
        *_fit_section("自分のactive task（最大5件）", _active_task_items(employee_id), budgets["tasks"], "- 明示タスクなし"),
        "",
        *_fit_section("関連する直近Discordログ（最大10件）", _related_recent_logs(employee_id), budgets["logs"], "- 関連ログなし"),
        "",
        *_fit_section("新規成果物（最大5件）", _new_artifacts(employee_id), budgets["artifacts"], "- 新規成果物なし"),
        "",
        *_fit_section("継続記憶（短縮）", _continuity_snippets(employee_id, mode), budgets["continuity"], "- なし"),
        "",
        "## 許可された行動",
        "- 自分の人格・役割で判断し、必要ならDiscordに短く投稿する",
        "- 雑談から有用な仮説や横断アイデアが出たら、行頭に [IDEA] を付ける",
        "- 必要なら成果物ファイルを作成・更新する",
        "- 他社員を呼ぶ時は @表示名 を使う。ただし1応答で呼ぶ相手は原則2人まで",
        "- 長文説明より、要約と成果物ファイルパスを優先する",
        "- 投稿/公開/確認をいくとへ依頼しない。Output Routesのどれかへ出すか、失敗理由と代替公開パスを成果物報告へ残す",
        "",
        *_fit_section(
            "全社員必読エッセンス（短縮）",
            _wisdom_items(budgets["wisdom"]),
            budgets["wisdom"],
            "- なし",
        ),
    ]
    digest = "\n".join(sections).strip()
    if len(digest) > MAX_DIGEST_CHARS:
        digest = digest[: MAX_DIGEST_CHARS - 42].rstrip() + "\n...(truncated: low priority tail omitted)"
    return digest


def should_wake_employee(employee_id: str) -> tuple[bool, int, str]:
    """Cheap preflight for autonomy loops before paying for an LLM call."""
    score = 0
    reasons: list[str] = []

    mentions = _recent_mentions(employee_id, max_items=3)
    if mentions:
        score += 4
        reasons.append("自分宛メンションあり")

    tasks = _active_task_items(employee_id, max_items=3)
    if tasks:
        score += 3
        reasons.append("active taskあり")

    logs = _related_recent_logs(employee_id, max_items=4, after_last_out=True)
    if logs:
        score += 1
        reasons.append("関連ログあり")

    artifacts = _new_artifacts(employee_id, max_items=3)
    if artifacts:
        score += 1
        reasons.append("新規成果物あり")

    try:
        from .revenue_ops import revenue_wake_items

        revenue_items = revenue_wake_items(employee_id, max_items=2)
    except Exception:
        revenue_items = []
    if revenue_items:
        score += 2
        reasons.append("自分に関係するRevenue実験あり")

    try:
        from .release_board import release_wake_items

        release_items = release_wake_items(employee_id, max_items=2)
    except Exception:
        release_items = []
    if release_items:
        score += 3
        reasons.append("公開待ち成果物あり")

    threshold = 3
    if employee_id in {"morinaga_haru", "saegusa_mio"}:
        threshold = 2
    return score >= threshold, score, ", ".join(reasons) or "起床理由なし"


def write_usage_metric(
    *,
    employee_id: str,
    mode: str,
    reason: str,
    prompt_chars: int = 0,
    response_chars: int = 0,
    used_resume: bool = False,
    model: Optional[str] = None,
    effort: Optional[str] = None,
    route_tier: Optional[str] = None,
    route_reason: Optional[str] = None,
    route_escalated: Optional[bool] = None,
    fallback_model: Optional[str] = None,
    chain_id: Optional[str] = None,
    depth: Optional[int] = None,
    skipped_reason: Optional[str] = None,
    latency_ms: Optional[int] = None,
) -> None:
    COMPANY_DIR.mkdir(parents=True, exist_ok=True)
    entry = {
        "ts": now_jst_iso(),
        "employee_id": employee_id,
        "mode": mode,
        "reason": _short(reason, 500),
        "prompt_chars": prompt_chars,
        "response_chars": response_chars,
        "used_resume": used_resume,
        "model": model,
        "effort": effort,
        "route_tier": route_tier,
        "route_reason": _short(route_reason or "", 300) if route_reason else None,
        "route_escalated": route_escalated,
        "fallback_model": fallback_model,
        "chain_id": chain_id,
        "depth": depth,
        "skipped_reason": skipped_reason,
        "latency_ms": latency_ms,
    }
    with USAGE_METRICS_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    _trim_usage_metrics_if_needed()


def _trim_usage_metrics_if_needed() -> None:
    try:
        if not USAGE_METRICS_PATH.exists() or USAGE_METRICS_PATH.stat().st_size < USAGE_METRICS_MAX_BYTES:
            return
        cutoff = datetime.now(JST) - timedelta(hours=USAGE_METRICS_RETENTION_HOURS)
        kept: list[str] = []
        for line in USAGE_METRICS_PATH.read_text(encoding="utf-8", errors="replace").splitlines():
            try:
                event = json.loads(line)
                ts = datetime.fromisoformat(event.get("ts", ""))
                if ts.tzinfo is None:
                    ts = ts.replace(tzinfo=JST)
                if ts >= cutoff:
                    kept.append(line)
            except Exception:
                continue
        kept = kept[-USAGE_METRICS_MAX_LINES:]
        USAGE_METRICS_PATH.write_text("\n".join(kept) + ("\n" if kept else ""), encoding="utf-8")
    except Exception:
        pass


def check_recent_token_pace(window_minutes: int = 60) -> dict:
    """直近 window_minutes の prompt_chars / response_chars / 呼び出し回数を集計。

    Returns:
        {
            "window_minutes": int,
            "total_calls": int,
            "skipped_calls": int,
            "executed_calls": int,
            "prompt_chars": int,
            "response_chars": int,
            "by_employee": {emp: prompt_chars},
            "top_employee": (emp, chars) or None,
        }
    """
    cutoff = datetime.now(JST) - timedelta(minutes=window_minutes)
    total = skipped = executed = 0
    prompt_chars = response_chars = 0
    by_employee: dict[str, int] = {}
    for event in _read_jsonl(USAGE_METRICS_PATH, limit=20000):
        try:
            ts = datetime.fromisoformat(event["ts"])
        except (KeyError, ValueError):
            continue
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=JST)
        if ts < cutoff:
            continue
        total += 1
        if event.get("skipped_reason"):
            skipped += 1
            continue
        executed += 1
        pc = int(event.get("prompt_chars") or 0)
        rc = int(event.get("response_chars") or 0)
        prompt_chars += pc
        response_chars += rc
        emp = str(event.get("employee_id", "?"))
        by_employee[emp] = by_employee.get(emp, 0) + pc
    top = max(by_employee.items(), key=lambda x: x[1]) if by_employee else None
    return {
        "window_minutes": window_minutes,
        "total_calls": total,
        "skipped_calls": skipped,
        "executed_calls": executed,
        "prompt_chars": prompt_chars,
        "response_chars": response_chars,
        "by_employee": by_employee,
        "top_employee": top,
    }


def write_usage_report(days: int = 1) -> Path:
    cutoff = datetime.now(JST) - timedelta(days=days)
    rows = []
    for event in _read_jsonl(USAGE_METRICS_PATH, limit=20000):
        try:
            ts = datetime.fromisoformat(event["ts"])
        except (KeyError, ValueError):
            continue
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=JST)
        if ts >= cutoff:
            rows.append(event)

    by_mode = Counter(str(r.get("mode", "?")) for r in rows)
    by_emp = Counter(str(r.get("employee_id", "?")) for r in rows)
    by_model = Counter(str(r.get("model", "?")) for r in rows if r.get("model"))
    by_effort = Counter(str(r.get("effort", "?")) for r in rows if r.get("effort"))
    by_route_tier = Counter(str(r.get("route_tier", "?")) for r in rows if r.get("route_tier"))
    skipped = sum(1 for r in rows if r.get("skipped_reason"))
    prompt_chars = sum(int(r.get("prompt_chars") or 0) for r in rows)
    response_chars = sum(int(r.get("response_chars") or 0) for r in rows)
    resume_count = sum(1 for r in rows if r.get("used_resume"))

    lines = [
        "# Usage Report",
        "",
        f"- window_days: {days}",
        f"- calls_or_skips: {len(rows)}",
        f"- skipped: {skipped}",
        f"- used_resume: {resume_count}",
        f"- prompt_chars_est: {prompt_chars}",
        f"- response_chars: {response_chars}",
        "",
        "## By mode",
        *[f"- {mode}: {count}" for mode, count in by_mode.most_common()],
        "",
        "## By model",
        *[f"- {model}: {count}" for model, count in by_model.most_common()],
        "",
        "## By effort",
        *[f"- {effort}: {count}" for effort, count in by_effort.most_common()],
        "",
        "## By route tier",
        *[f"- {tier}: {count}" for tier, count in by_route_tier.most_common()],
        "",
        "## By employee",
        *[f"- {emp}: {count}" for emp, count in by_emp.most_common()],
    ]
    USAGE_REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return USAGE_REPORT_PATH
