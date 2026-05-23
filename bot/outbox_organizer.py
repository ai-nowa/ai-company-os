"""社員の outbox を整理する watcher。

目的: `business_plan_v0.1.md` ... `v0.4.md` のように同一トピックの複数版が
outbox に積み上がる状態を解消し、「最新版がどれか」を明確にする。

仕組み:
1. 各社員の outbox/ を走査
2. ファイル名から「topic_v{N}」パターンを抽出（例: 2026-05-17_business_plan_v0.4.md → topic=business_plan, ver=v0.4）
3. 同一 topic で複数版あれば、最新版以外を outbox/_archive/ に移動
4. outbox/INDEX.md を生成（最新版・version 履歴・サイズを一覧）
5. 1時間ごとに自動実行（LLM 呼ばない）
"""
from __future__ import annotations

import asyncio
import logging
import re
import shutil
from datetime import datetime
from pathlib import Path

from .config import BASE_DIR, EMPLOYEES, JST
from . import dynamic_config

log = logging.getLogger("outbox_organizer")

# パターン: 「日付_topic_v{N}.md」or「topic_v{N}.md」
VERSION_RE = re.compile(r"(?P<prefix>.*?)_v(?P<ver>[0-9]+(?:\.[0-9]+)?)\.md$")


def _extract_topic_version(filename: str) -> tuple[str, str] | None:
    """ファイル名から (topic, version) を返す。version パターンなしなら None"""
    m = VERSION_RE.match(filename)
    if not m:
        return None
    prefix = m.group("prefix")
    # 日付プレフィックス（YYYY-MM-DD_）を除去
    prefix = re.sub(r"^\d{4}-\d{2}-\d{2}_", "", prefix)
    ver = m.group("ver")
    return prefix, ver


def _version_key(ver: str) -> tuple[int, ...]:
    """'0.4' → (0, 4), '1' → (1,)"""
    return tuple(int(p) for p in ver.split("."))


def organize_one_outbox(emp_id: str) -> dict:
    """1社員の outbox を整理。INDEX.md を生成し、古い版を _archive/ へ"""
    from .config import employee_home
    home = employee_home(emp_id)
    outbox = home / "outbox"
    if not outbox.exists():
        return {"emp_id": emp_id, "archived": 0, "indexed": 0, "skipped": True}

    archive = outbox / "_archive"
    archive.mkdir(exist_ok=True)

    # トピックごとにバージョンを集める
    topics: dict[str, list[tuple[str, Path]]] = {}
    other_files: list[Path] = []
    for f in outbox.iterdir():
        if not f.is_file() or f.suffix != ".md":
            continue
        if f.name == "INDEX.md":
            continue
        tv = _extract_topic_version(f.name)
        if tv is None:
            other_files.append(f)
            continue
        topic, ver = tv
        topics.setdefault(topic, []).append((ver, f))

    archived = 0
    latest_by_topic: dict[str, Path] = {}
    archived_by_topic: dict[str, list[Path]] = {}

    for topic, versions in topics.items():
        versions.sort(key=lambda x: _version_key(x[0]), reverse=True)
        latest_ver, latest_path = versions[0]
        latest_by_topic[topic] = latest_path
        for ver, path in versions[1:]:
            target = archive / path.name
            try:
                shutil.move(str(path), str(target))
                archived += 1
                archived_by_topic.setdefault(topic, []).append(target)
            except Exception:
                log.exception(f"archive failed: {path}")

    # INDEX.md 生成
    index_lines = [
        f"# {EMPLOYEES.get(emp_id, {}).get('display', emp_id)} の outbox INDEX",
        "",
        f"自動生成: {datetime.now(JST).strftime('%Y-%m-%d %H:%M')} JST",
        "",
        "## 最新版（version 付きトピック）",
        "",
    ]
    if latest_by_topic:
        for topic in sorted(latest_by_topic):
            p = latest_by_topic[topic]
            size = p.stat().st_size
            mtime = datetime.fromtimestamp(p.stat().st_mtime, JST).strftime("%m-%d %H:%M")
            archived_list = archived_by_topic.get(topic, [])
            archived_note = f" (旧版 {len(archived_list)} 個 _archive/ へ)" if archived_list else ""
            index_lines.append(f"- **{topic}** — `{p.name}` ({size}B / {mtime}){archived_note}")
    else:
        index_lines.append("（version 付きファイルなし）")

    if other_files:
        index_lines.extend(["", "## その他ファイル（version 無し）", ""])
        for f in sorted(other_files, key=lambda x: x.stat().st_mtime, reverse=True):
            size = f.stat().st_size
            mtime = datetime.fromtimestamp(f.stat().st_mtime, JST).strftime("%m-%d %H:%M")
            index_lines.append(f"- `{f.name}` ({size}B / {mtime})")

    # _archive 一覧（参考、件数のみ）
    archived_files = list(archive.glob("*.md"))
    if archived_files:
        index_lines.extend([
            "",
            f"## _archive/（{len(archived_files)} 個）",
            "",
            f"古いバージョンは `outbox/_archive/` に格納。必要なら参照可。",
        ])

    (outbox / "INDEX.md").write_text("\n".join(index_lines) + "\n", encoding="utf-8")
    return {
        "emp_id": emp_id,
        "archived": archived,
        "indexed": len(latest_by_topic),
        "other_files": len(other_files),
    }


def organize_all() -> list[dict]:
    results = []
    for emp_id in EMPLOYEES.keys():
        try:
            results.append(organize_one_outbox(emp_id))
        except Exception:
            log.exception(f"organize failed for {emp_id}")
            results.append({"emp_id": emp_id, "error": True})
    return results


async def organizer_loop() -> None:
    interval = dynamic_config.get("outbox_organizer.interval_seconds", 3600)
    log.info(f"outbox_organizer started (interval={interval}s = {interval//60}min)")
    while True:
        try:
            interval = dynamic_config.get("outbox_organizer.interval_seconds", 3600)
            await asyncio.sleep(interval)
            results = organize_all()
            total_archived = sum(r.get("archived", 0) for r in results)
            total_indexed = sum(r.get("indexed", 0) for r in results)
            if total_archived > 0:
                log.info(f"outbox_organizer: archived={total_archived}, indexed={total_indexed}")
            else:
                log.info(f"outbox_organizer: no archive needed, indexed={total_indexed}")
        except asyncio.CancelledError:
            return
        except Exception:
            log.exception("outbox_organizer loop error")
            await asyncio.sleep(interval)


if __name__ == "__main__":
    # 単体テスト
    import json
    results = organize_all()
    print(json.dumps(results, ensure_ascii=False, indent=2))
