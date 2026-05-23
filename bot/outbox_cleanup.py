"""outbox_cleanup.py — 9社員 outbox の自動アーカイブ + 月次統計レポート。

各社員の outbox/ 配下で最終更新が ARCHIVE_DAYS 日を超えたファイルを
outbox/_archive/ に移動する。

使い方:
  python -m bot.outbox_cleanup          # dry-run（移動しない、件数だけ表示）
  python -m bot.outbox_cleanup --run    # 実行（実際に移動）
  python -m bot.outbox_cleanup --stats  # 現在の件数統計のみ
"""
from __future__ import annotations

import logging
import shutil
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path

log = logging.getLogger("outbox_cleanup")

ARCHIVE_DAYS = 7
EMPLOYEES_DIR = Path(__file__).parent.parent / "employees"
EMPLOYEE_IDS = [
    "arima_reiji",
    "asakura_noa",
    "hinata_nagi",
    "hoshino_ritsu",
    "kagura_aoi",
    "kuroba_yuu",
    "morinaga_haru",
    "saegusa_mio",
    "shirase_kai",
]
JST = timezone(timedelta(hours=9))


def _mtime_days_ago(path: Path) -> float:
    return (time.time() - path.stat().st_mtime) / 86400


_SKIP_NAMES = {".keep", ".gitkeep", ".gitignore"}


def collect_stale(emp_id: str) -> list[Path]:
    """指定社員の outbox から ARCHIVE_DAYS 超のファイルを収集（archive系と管理ファイル除く）"""
    outbox = EMPLOYEES_DIR / emp_id / "outbox"
    if not outbox.exists():
        return []
    return [
        p for p in outbox.iterdir()
        if p.is_file()
        and p.name not in _SKIP_NAMES
        and _mtime_days_ago(p) > ARCHIVE_DAYS
    ]


def run_cleanup(dry_run: bool = True) -> dict[str, dict]:
    """
    全社員の outbox を走査してアーカイブ。
    戻り値: {emp_id: {"moved": int, "skipped": int, "errors": int}}
    """
    results: dict[str, dict] = {}
    for emp_id in EMPLOYEE_IDS:
        stale = collect_stale(emp_id)
        moved = skipped = errors = 0
        archive_dir = EMPLOYEES_DIR / emp_id / "outbox" / "_archive"

        for src in stale:
            dest = archive_dir / src.name
            if dry_run:
                log.info("[dry-run] would move: %s", src)
                skipped += 1
                continue
            try:
                archive_dir.mkdir(parents=True, exist_ok=True)
                # 同名ファイルが既にあれば末尾にタイムスタンプを付ける
                if dest.exists():
                    ts = datetime.now(JST).strftime("%Y%m%dT%H%M%S")
                    dest = archive_dir / f"{src.stem}_{ts}{src.suffix}"
                shutil.move(str(src), str(dest))
                log.info("archived: %s -> %s", src.name, dest)
                moved += 1
            except Exception as exc:
                log.error("failed to move %s: %s", src, exc)
                errors += 1

        results[emp_id] = {"moved": moved, "skipped": skipped, "errors": errors}
    return results


def current_stats() -> dict[str, int]:
    """社員別の現在の outbox ファイル数（archive系と管理ファイル除く）"""
    stats: dict[str, int] = {}
    for emp_id in EMPLOYEE_IDS:
        outbox = EMPLOYEES_DIR / emp_id / "outbox"
        if not outbox.exists():
            stats[emp_id] = 0
            continue
        stats[emp_id] = sum(
            1 for p in outbox.iterdir()
            if p.is_file() and p.name not in _SKIP_NAMES
        )
    return stats


def format_report(before: dict[str, int], results: dict[str, dict]) -> str:
    """経営会議報告用テキスト（markdown）"""
    now = datetime.now(JST).strftime("%Y-%m-%d %H:%M JST")
    lines = [f"## outbox クリーンアップ完了 ({now})", ""]
    total_moved = sum(v["moved"] for v in results.values())
    total_before = sum(before.values())
    lines.append(f"**移動済み**: {total_moved} ファイル")
    lines.append(f"**クリーン前合計**: {total_before} ファイル")
    lines.append("")
    lines.append("| 社員 | 前 | 移動 | エラー |")
    lines.append("|------|----|------|--------|")
    for emp_id in EMPLOYEE_IDS:
        r = results.get(emp_id, {})
        lines.append(
            f"| {emp_id} | {before.get(emp_id, 0)} "
            f"| {r.get('moved', 0)} | {r.get('errors', 0)} |"
        )
    return "\n".join(lines)


async def run_cleanup_async(dry_run: bool = False) -> str:
    """daily_loop から呼ぶ非同期ラッパー。報告テキストを返す。"""
    import asyncio
    loop = asyncio.get_event_loop()
    before = await loop.run_in_executor(None, current_stats)
    results = await loop.run_in_executor(None, run_cleanup, dry_run)
    return format_report(before, results)


if __name__ == "__main__":
    import sys

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    args = set(sys.argv[1:])
    if "--stats" in args:
        stats = current_stats()
        print("=== outbox current stats ===")
        for emp, cnt in sorted(stats.items(), key=lambda x: -x[1]):
            print(f"  {emp:20s}: {cnt}")
        print(f"  {'TOTAL':20s}: {sum(stats.values())}")
    elif "--run" in args:
        before = current_stats()
        results = run_cleanup(dry_run=False)
        print(format_report(before, results))
    else:
        before = current_stats()
        print("=== DRY RUN (pass --run to execute) ===")
        results = run_cleanup(dry_run=True)
        print(format_report(before, results))
