"""Lightweight employee activity index.

Conversation logs are periodically compressed into ``session/archive``.  Any
health check that only reads the current ``conversation_log.jsonl`` can then
misclassify an active employee as idle.  This module centralizes the cheap
"latest activity" reads so dashboards and self-improvement checks agree.
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Iterable, Iterator, Optional

from .config import BASE_DIR, EMPLOYEES, JST


def parse_ts(value: str | None) -> Optional[datetime]:
    if not value:
        return None
    try:
        ts = datetime.fromisoformat(value)
    except (TypeError, ValueError):
        return None
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=JST)
    return ts


def _employee_home(employee_id: str) -> Path:
    return BASE_DIR / "employees" / employee_id


def employee_log_paths(employee_id: str, archive_limit: int = 6) -> list[Path]:
    """Return current log plus newest archive logs for an employee."""
    session_dir = _employee_home(employee_id) / "session"
    paths: list[Path] = []
    current = session_dir / "conversation_log.jsonl"
    if current.exists():
        paths.append(current)

    archive_dir = session_dir / "archive"
    if archive_dir.exists():
        archives = sorted(
            archive_dir.glob("conversation_log*.jsonl"),
            key=lambda p: p.stat().st_mtime if p.exists() else 0,
            reverse=True,
        )
        paths.extend(archives[:archive_limit])
    return paths


def iter_employee_events(
    employee_id: str,
    *,
    since: Optional[datetime] = None,
    kinds: Optional[Iterable[str]] = None,
    archive_limit: int = 6,
) -> Iterator[dict]:
    """Yield employee log events from current and recent archive files."""
    kind_set = set(kinds) if kinds else None
    seen: set[tuple[str, str, str]] = set()
    for path in employee_log_paths(employee_id, archive_limit=archive_limit):
        try:
            lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            continue
        for line in lines:
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            if kind_set and event.get("kind") not in kind_set:
                continue
            ts_text = str(event.get("ts", ""))
            ts = parse_ts(ts_text)
            if since and (ts is None or ts < since):
                continue
            key = (ts_text, str(event.get("kind", "")), str(event.get("text", ""))[:120])
            if key in seen:
                continue
            seen.add(key)
            event["_emp"] = employee_id
            yield event


def iter_all_employee_events(
    *,
    since: Optional[datetime] = None,
    kinds: Optional[Iterable[str]] = None,
    archive_limit: int = 6,
) -> Iterator[dict]:
    for employee_id in EMPLOYEES:
        yield from iter_employee_events(
            employee_id,
            since=since,
            kinds=kinds,
            archive_limit=archive_limit,
        )


def last_employee_out_ts(employee_id: str, archive_limit: int = 10) -> str:
    """Return the latest successful employee response timestamp.

    ``session_state.last_active`` is a valid fallback because employee_runner
    writes it only after a successful model response has been logged.
    """
    latest = ""
    for event in iter_employee_events(
        employee_id,
        kinds={"out"},
        archive_limit=archive_limit,
    ):
        ts = str(event.get("ts", ""))
        if ts > latest:
            latest = ts

    state_path = _employee_home(employee_id) / "session" / "session_state.json"
    try:
        state = json.loads(state_path.read_text(encoding="utf-8"))
        last_active = str(state.get("last_active", ""))
        if last_active > latest:
            latest = last_active
    except (FileNotFoundError, json.JSONDecodeError):
        pass
    return latest
