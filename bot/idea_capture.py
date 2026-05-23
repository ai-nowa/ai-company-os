"""Capture useful ideas from employee Discord posts.

Small talk is valuable only when it can occasionally create new options.
Employees can mark those moments with [IDEA], and the system records them
without spending another LLM call.
"""
from __future__ import annotations

import re

from .config import COMPANY_DIR, EMPLOYEES, now_jst_iso
from .revenue_ops import append_idea_to_experiment_inbox

IDEA_RE = re.compile(
    r"^\s*(?:\[IDEA\]|IDEA:|アイデア[:：])\s*(.+?)\s*$",
    re.IGNORECASE | re.MULTILINE,
)


def capture_ideas_from_text(employee_id: str, channel: str, text: str) -> int:
    ideas = [m.group(1).strip() for m in IDEA_RE.finditer(text) if m.group(1).strip()]
    if not ideas:
        return 0

    COMPANY_DIR.mkdir(parents=True, exist_ok=True)
    path = COMPANY_DIR / "idea_log.md"
    if not path.exists():
        path.write_text("# Idea Log\n\n", encoding="utf-8")

    display = EMPLOYEES.get(employee_id, {}).get("display", employee_id)
    with path.open("a", encoding="utf-8") as f:
        for idea in ideas:
            f.write(
                f"## {now_jst_iso()} / {display} / #{channel}\n\n"
                f"{idea}\n\n"
            )
            try:
                append_idea_to_experiment_inbox(employee_id, channel, idea)
            except Exception:
                pass
    return len(ideas)
