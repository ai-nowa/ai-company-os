from __future__ import annotations

from pathlib import Path

import bot.revenue_ops as ro
from bot.idea_capture import capture_ideas_from_text


def _redirect_revenue_paths(monkeypatch, tmp_path: Path) -> Path:
    company_dir = tmp_path / "company"
    monkeypatch.setattr(ro, "COMPANY_DIR", company_dir)
    monkeypatch.setattr(ro, "REVENUE_BOARD_PATH", company_dir / "revenue_board.md")
    monkeypatch.setattr(ro, "EXPERIMENT_BACKLOG_PATH", company_dir / "experiment_backlog.md")
    monkeypatch.setattr(ro, "DAILY_CLOSE_PATH", company_dir / "daily_close.md")
    monkeypatch.setattr(ro, "DECISION_BRIEFS_DIR", company_dir / "decision_briefs")
    monkeypatch.setattr(ro, "DECISION_BRIEFS_README_PATH", company_dir / "decision_briefs" / "README.md")
    return company_dir


def test_ensure_revenue_ops_files_creates_core_docs(monkeypatch, tmp_path):
    company_dir = _redirect_revenue_paths(monkeypatch, tmp_path)

    ro.ensure_revenue_ops_files()

    assert (company_dir / "revenue_board.md").exists()
    assert (company_dir / "experiment_backlog.md").exists()
    assert (company_dir / "daily_close.md").exists()
    assert (company_dir / "decision_briefs" / "README.md").exists()


def test_revenue_digest_is_compact_and_employee_filtered(monkeypatch, tmp_path):
    _redirect_revenue_paths(monkeypatch, tmp_path)
    ro.ensure_revenue_ops_files()

    digest = ro.revenue_digest(max_chars=700, employee_id="kuroba_yuu")

    assert len(digest) <= 700
    assert "EXP-001" in digest
    assert "EXP-002" not in digest


def test_idea_capture_appends_to_experiment_inbox(monkeypatch, tmp_path):
    company_dir = _redirect_revenue_paths(monkeypatch, tmp_path)
    monkeypatch.setattr("bot.idea_capture.COMPANY_DIR", company_dir)

    count = capture_ideas_from_text(
        "morinaga_haru",
        "給湯室",
        "[IDEA] 雑談からAI社員OSの導入支援商品を作る",
    )
    count_again = capture_ideas_from_text(
        "morinaga_haru",
        "給湯室",
        "[IDEA] 雑談からAI社員OSの導入支援商品を作る",
    )

    backlog = ro.EXPERIMENT_BACKLOG_PATH.read_text(encoding="utf-8")
    assert count == 1
    assert count_again == 1
    assert backlog.count("雑談からAI社員OSの導入支援商品を作る") == 1
    assert "status: inbox" in backlog
