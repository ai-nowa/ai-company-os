from pathlib import Path

from bot import context_assembler
from bot.context_assembler import assemble_state_digest, should_wake_employee
from bot.employee_autonomy import build_self_prompt
from bot.employee_runner import build_employee_system_prompt


def test_prompts_treat_due_dates_as_deadlines_not_wait_dates() -> None:
    system_prompt = build_employee_system_prompt("arima_reiji")
    self_prompt = build_self_prompt("saegusa_mio")

    assert "待機日ではなく最遅締切" in system_prompt
    assert "next_action_now" in system_prompt
    assert "日付・期限の扱い（待機化禁止）" in self_prompt
    assert "判定日まで静観" in self_prompt


def test_state_digest_includes_deadline_rule_within_budget() -> None:
    digest = assemble_state_digest("saegusa_mio", "期限付きタスク確認", mode="routine")

    assert "## 期限の読み方（待機禁止）" in digest
    assert "待機日ではなく最遅締切" in digest
    assert "next_action_now" in digest
    assert len(digest) <= context_assembler.MAX_DIGEST_CHARS


def test_active_task_summary_adds_next_action_fallback(
    monkeypatch, tmp_path: Path
) -> None:
    company_dir = tmp_path / "company"
    company_dir.mkdir()
    (company_dir / "active_tasks.md").write_text(
        """# Active Tasks

## 現在のタスク

```yaml
id: T-TEST
title: 期限を待機にしない検証
owner: hoshino_ritsu
reviewer: hinata_nagi
buddy: morinaga_haru
status: in_progress
priority: P1
due: 2026-06-01
```
""",
        encoding="utf-8",
    )

    monkeypatch.setattr(context_assembler, "COMPANY_DIR", company_dir)

    items = context_assembler._active_task_items("hoshino_ritsu")

    assert len(items) == 1
    assert "due: 2026-06-01" in items[0]
    assert "next_action_now: due前に今できる準備" in items[0]


def test_active_task_alone_is_enough_to_wake_employee(monkeypatch) -> None:
    monkeypatch.setattr(context_assembler, "_recent_mentions", lambda *args, **kwargs: [])
    monkeypatch.setattr(
        context_assembler,
        "_active_task_items",
        lambda *args, **kwargs: ["- id: T-TEST / status: in_progress / due: 2026-06-01"],
    )
    monkeypatch.setattr(context_assembler, "_related_recent_logs", lambda *args, **kwargs: [])
    monkeypatch.setattr(context_assembler, "_new_artifacts", lambda *args, **kwargs: [])

    import bot.revenue_ops as revenue_ops

    monkeypatch.setattr(revenue_ops, "revenue_wake_items", lambda *args, **kwargs: [])

    should_wake, score, reason = should_wake_employee("hoshino_ritsu")

    assert should_wake is True
    assert score >= 3
    assert "active taskあり" in reason
