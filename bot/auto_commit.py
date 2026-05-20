"""shared/docs/ などの成果物を git に自動 commit する。

目的:
- 履歴の保存（誰が・いつ・何を変えたか）
- ロールバック可能化
- 公開（GitHub push）の前準備

仕組み:
- 1時間ごとに git add → diff があれば commit
- 対象: shared/docs/, shared/decisions/, company/active_tasks.md, shared/dependencies.md, shared/dashboard.md
- push はしない（手動で）
"""
from __future__ import annotations

import asyncio
import logging
import subprocess
from datetime import datetime
from pathlib import Path

from .config import BASE_DIR, JST
from . import dynamic_config

log = logging.getLogger("auto_commit")
COMMIT_PATHS = [
    "shared/docs",
    "shared/decisions",
    "company/active_tasks.md",
    "shared/dependencies.md",
    "shared/dashboard.md",
    "company/decision_matrix.md",
    "company/shared_docs_promotion.md",
    "company/owner_request_protocol.md",
]


def _run(cmd: list[str], cwd: Path = BASE_DIR) -> tuple[int, str]:
    try:
        r = subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True, timeout=30)
        return r.returncode, (r.stdout + r.stderr).strip()
    except Exception as e:
        return -1, str(e)


def has_changes() -> bool:
    """対象パスに staged or unstaged な変更があるか"""
    rc, out = _run(["git", "status", "--porcelain"] + COMMIT_PATHS)
    return bool(out.strip())


def do_commit() -> tuple[bool, str]:
    # add
    rc, out = _run(["git", "add"] + COMMIT_PATHS)
    if rc != 0:
        return False, f"git add failed: {out}"
    # commit (diff --cached で staged があるかチェック)
    rc, out = _run(["git", "diff", "--cached", "--quiet"])
    if rc == 0:
        return False, "no staged changes"  # 変更なし
    msg = f"auto: {datetime.now(JST).strftime('%Y-%m-%d %H:%M')} (architect_auto_commit)"
    rc, out = _run(["git", "commit", "-m", msg, "--no-verify"])
    if rc != 0:
        return False, f"commit failed: {out[:200]}"
    return True, msg


async def commit_loop() -> None:
    interval = dynamic_config.get("auto_commit.interval_seconds", 3600)
    log.info(f"auto_commit started (interval={interval}s = {interval//60}min)")
    while True:
        try:
            interval = dynamic_config.get("auto_commit.interval_seconds", 3600)
            await asyncio.sleep(interval)
            if not has_changes():
                continue
            ok, msg = do_commit()
            if ok:
                log.info(f"auto_commit: {msg}")
            else:
                log.info(f"auto_commit: skipped ({msg})")
        except asyncio.CancelledError:
            return
        except Exception:
            log.exception("auto_commit loop error")
            await asyncio.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    print(f"has_changes: {has_changes()}")
    ok, msg = do_commit()
    print(f"commit: ok={ok} msg={msg}")
