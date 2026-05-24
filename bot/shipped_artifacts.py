"""Persistent shipped-artifact ledger.

This is the missing bridge between "a file exists" and "the company already
turned it into a public, measurable output".  It is intentionally JSONL so the
dispatcher can append without rewriting large state files.
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from .config import BASE_DIR, COMPANY_DIR, JST, now_jst_iso

LEDGER_PATH = COMPANY_DIR / "shipped_artifacts.jsonl"


def _normalize_path(value: str | Path) -> str:
    raw = str(value).strip()
    path = Path(raw)
    if not path.is_absolute():
        return raw
    try:
        return str(path.resolve().relative_to(BASE_DIR))
    except Exception:
        return raw


def _parse_ts(value: str) -> datetime | None:
    if not value:
        return None
    try:
        ts = datetime.fromisoformat(value)
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=JST)
        return ts.astimezone(JST)
    except Exception:
        return None


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(item, dict):
            rows.append(item)
    return rows


def load_shipped_artifacts(hours: int | None = None, limit: int = 2000) -> list[dict[str, Any]]:
    rows = _read_jsonl(LEDGER_PATH)[-limit:]
    if hours is None:
        return rows
    cutoff = datetime.now(JST) - timedelta(hours=hours)
    kept: list[dict[str, Any]] = []
    for row in rows:
        ts = _parse_ts(str(row.get("verified_at") or row.get("ts") or ""))
        if ts and ts >= cutoff:
            kept.append(row)
    return kept


def _row_paths(row: dict[str, Any]) -> set[str]:
    paths = set()
    for key in ("source_path", "output_path"):
        value = str(row.get(key) or "").strip()
        if value:
            paths.add(_normalize_path(value))
    supersedes = row.get("supersedes") or []
    if isinstance(supersedes, str):
        supersedes = [supersedes]
    for value in supersedes:
        if str(value).strip():
            paths.add(_normalize_path(str(value)))
    return paths


def source_is_shipped(source_path: str | Path) -> bool:
    target = _normalize_path(source_path)
    return any(target in _row_paths(row) for row in load_shipped_artifacts())


def record_shipped_artifact(
    *,
    source_path: str | Path,
    route: str,
    output_url: str,
    executor: str = "",
    output_path: str | Path | None = None,
    title: str = "",
    verified_at: str | None = None,
    supersedes: list[str] | None = None,
    evidence: str = "",
) -> dict[str, Any]:
    """Append a shipped artifact unless the same source/url already exists."""
    source = _normalize_path(source_path)
    url = str(output_url).strip()
    rows = load_shipped_artifacts()
    for row in rows:
        if row.get("source_path") == source and row.get("output_url") == url:
            return row

    item: dict[str, Any] = {
        "ts": now_jst_iso(),
        "verified_at": verified_at or now_jst_iso(),
        "source_path": source,
        "route": route,
        "output_url": url,
        "executor": executor,
        "title": title,
        "supersedes": [_normalize_path(p) for p in (supersedes or [])],
        "evidence": evidence,
    }
    if output_path:
        item["output_path"] = _normalize_path(output_path)

    LEDGER_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LEDGER_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(item, ensure_ascii=False, sort_keys=True) + "\n")
    return item


def _topic_keys_from_text(text: str) -> set[str]:
    text = text.lower()
    keys: set[str] = set()
    for m in re.findall(r"exp[-_]?(\d{3})", text):
        keys.update({f"exp-{m}", f"exp{m}"})
    for m in re.findall(r"article[-_]?(\d{1,3})", text):
        n = int(m)
        keys.update({f"article-{n:02d}", f"article{n:02d}", f"article-{n}", f"article{n}"})
    for seg in re.findall(r"/(?:notes|articles)/([a-z0-9][a-z0-9\-]{3,})/?", text):
        keys.add(seg)
    return keys


def shipped_topic_keys(hours: int | None = None) -> set[str]:
    keys: set[str] = set()
    for row in load_shipped_artifacts(hours=hours):
        blob = " ".join(
            str(row.get(k, ""))
            for k in ("source_path", "output_path", "output_url", "title", "evidence")
        )
        keys.update(_topic_keys_from_text(blob))
        for value in row.get("supersedes") or []:
            keys.update(_topic_keys_from_text(str(value)))
    return keys


def shipped_digest(max_chars: int = 600) -> str:
    rows = list(reversed(load_shipped_artifacts(hours=72, limit=100)))
    if not rows:
        return "- shipped ledger: empty"
    lines = [f"- shipped ledger 72h: {len(rows)}"]
    for row in rows[:5]:
        src = row.get("source_path", "?")
        url = row.get("output_url", "?")
        route = row.get("route", "?")
        lines.append(f"- {route}: {src} -> {url}")
    text = "\n".join(lines)
    if len(text) <= max_chars:
        return text
    return text[: max(0, max_chars - 16)].rstrip() + "\n- ...(truncated)"
