"""会話ログ自動ローテーション。

conversation_log.jsonl が 100 KB を超えたら
session/archive/conversation_log_<JST timestamp>.jsonl にリネームし、
元ファイルを空にする。

対象: 9 社員 + founders/claude
"""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path

log = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).parent.parent
JST = timezone(timedelta(hours=9))

ROTATE_THRESHOLD_BYTES = 100 * 1024  # 100 KB

# 対象パス一覧 (employee_id → session dir)
def _session_dirs() -> list[tuple[str, Path]]:
    targets: list[tuple[str, Path]] = []
    emp_dir = REPO_ROOT / "employees"
    for emp_home in sorted(emp_dir.iterdir()):
        if emp_home.is_dir():
            targets.append((emp_home.name, emp_home / "session"))
    # founders/claude
    founders_claude = REPO_ROOT / "founders" / "claude" / "session"
    if founders_claude.parent.exists():
        targets.append(("founders/claude", founders_claude))
    return targets


def rotate_if_needed(label: str, session_dir: Path) -> bool:
    """session_dir/conversation_log.jsonl が閾値超なら rotate。True=実行。"""
    log_path = session_dir / "conversation_log.jsonl"
    if not log_path.exists():
        return False
    if log_path.stat().st_size < ROTATE_THRESHOLD_BYTES:
        return False

    archive_dir = session_dir / "archive"
    archive_dir.mkdir(parents=True, exist_ok=True)

    ts = datetime.now(JST).strftime("%Y%m%d_%H%M%S")
    archive_path = archive_dir / f"conversation_log_{ts}.jsonl"
    log_path.rename(archive_path)
    log_path.write_text("", encoding="utf-8")

    size_kb = archive_path.stat().st_size // 1024
    log.info(f"[log_rotator] {label}: rotated {size_kb}KB → {archive_path.name}")
    return True


def rotate_all() -> list[str]:
    """全対象を走査してローテ。実行されたラベルのリストを返す。"""
    rotated: list[str] = []
    for label, session_dir in _session_dirs():
        if rotate_if_needed(label, session_dir):
            rotated.append(label)
    return rotated


async def log_rotation_loop() -> None:
    """10分間隔で全対象のローテを実行する常駐コルーチン。"""
    await asyncio.sleep(60)  # 起動直後の余熱待ち
    while True:
        try:
            rotated = rotate_all()
            if rotated:
                log.info(f"[log_rotator] rotated {len(rotated)} logs: {rotated}")
        except Exception:
            log.exception("[log_rotator] rotate_all failed")
        await asyncio.sleep(600)  # 10分
