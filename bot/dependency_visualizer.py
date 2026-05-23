"""active_tasks.md の depends_on を解析してグラフ化する watcher。

目的:
- 「このタスクは何を待ってる？」「Aが終わったら何が動ける？」を見える化
- ボトルネックの可視化（多くのタスクが依存しているタスク）

仕組み:
- 1時間ごとに active_tasks.md を解析
- mermaid graph を shared/dependencies.md に書き出す
- LLM 呼ばない
"""
from __future__ import annotations

import asyncio
import logging
import re
from datetime import datetime
from pathlib import Path

from .config import BASE_DIR, JST
from . import dynamic_config

log = logging.getLogger("dependency_visualizer")

ACTIVE_TASKS = BASE_DIR / "company" / "active_tasks.md"
OUTPUT = BASE_DIR / "shared" / "dependencies.md"


def _parse_tasks() -> list[dict]:
    if not ACTIVE_TASKS.exists():
        return []
    text = ACTIVE_TASKS.read_text(encoding="utf-8", errors="replace")
    tasks: list[dict] = []
    in_yaml = False
    block: list[str] = []
    for line in text.splitlines():
        s = line.strip()
        if s.startswith("```yaml"):
            in_yaml = True
            block = []
            continue
        if s == "```" and in_yaml:
            bt = "\n".join(block)
            tid = re.search(r"id:\s*(\S+)", bt)
            title = re.search(r"title:\s*(.+)", bt)
            status = re.search(r"status:\s*(\S+)", bt)
            owner = re.search(r"owner:\s*(\S+)", bt)
            deps_match = re.search(r"depends_on:\s*\[(.*?)\]", bt)
            deps: list[str] = []
            if deps_match:
                inner = deps_match.group(1).strip()
                if inner:
                    deps = [d.strip().strip('"').strip("'") for d in inner.split(",") if d.strip()]
            if tid:
                tasks.append({
                    "id": tid.group(1).strip(),
                    "title": (title.group(1).strip() if title else "")[:50],
                    "status": (status.group(1).strip().lower() if status else "?"),
                    "owner": (owner.group(1).strip() if owner else "?"),
                    "deps": deps,
                })
            in_yaml = False
            block = []
            continue
        if in_yaml:
            block.append(line)
    return tasks


def _status_color(status: str) -> str:
    return {
        "done": "fill:#9f9",
        "in_progress": "fill:#ff9",
        "review": "fill:#9cf",
        "pending": "fill:#fff",
        "blocked": "fill:#f99",
    }.get(status, "fill:#ccc")


def render_mermaid(tasks: list[dict]) -> str:
    """tasks → mermaid graph + 説明"""
    now = datetime.now(JST).strftime("%Y-%m-%d %H:%M JST")
    lines = [
        "# タスク依存関係グラフ",
        "",
        f"自動生成: {now}",
        "",
        "ステータス色: 緑=done / 黄=in_progress / 青=review / 白=pending / 赤=blocked",
        "",
        "```mermaid",
        "graph TD",
    ]
    # ノード
    for t in tasks:
        label = f"{t['id']}<br/>{t['title']}<br/>{t['owner']}"
        lines.append(f"  {t['id']}[\"{label}\"]")
        lines.append(f"  style {t['id']} {_status_color(t['status'])}")
    # エッジ（A depends_on B → B が先、B --> A）
    has_edge = False
    for t in tasks:
        for dep in t["deps"]:
            if dep:
                lines.append(f"  {dep} --> {t['id']}")
                has_edge = True
    if not has_edge:
        lines.append("  %% no dependencies declared")
    lines.append("```")
    lines.append("")

    # ボトルネック分析（多くのタスクから依存される＝ボトルネック候補）
    deps_count: dict[str, int] = {}
    for t in tasks:
        for dep in t["deps"]:
            deps_count[dep] = deps_count.get(dep, 0) + 1
    if deps_count:
        lines.append("## ボトルネック候補（多くのタスクから依存される）")
        lines.append("")
        for tid, count in sorted(deps_count.items(), key=lambda x: -x[1])[:5]:
            t_match = next((t for t in tasks if t["id"] == tid), None)
            extra = f"（status={t_match['status']}, owner={t_match['owner']}）" if t_match else ""
            lines.append(f"- **{tid}**: {count} タスクが依存 {extra}")
        lines.append("")

    # 動ける状態
    movable = [t for t in tasks if t["status"] in ("pending", "in_progress", "review")]
    blocked_by_deps = []
    for t in movable:
        unmet = [d for d in t["deps"] if any(o["id"] == d and o["status"] not in ("done",) for o in tasks)]
        if unmet:
            blocked_by_deps.append((t, unmet))
    if blocked_by_deps:
        lines.append("## 依存先未完了で実質ブロック中")
        lines.append("")
        for t, unmet in blocked_by_deps[:10]:
            lines.append(f"- `{t['id']}` ({t['owner']}) is waiting for: {', '.join(unmet)}")
        lines.append("")

    return "\n".join(lines) + "\n"


def write_dependencies() -> Path:
    tasks = _parse_tasks()
    content = render_mermaid(tasks)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(content, encoding="utf-8")
    return OUTPUT


async def visualizer_loop() -> None:
    interval = dynamic_config.get("dependency_visualizer.interval_seconds", 3600)
    log.info(f"dependency_visualizer started (interval={interval}s)")
    while True:
        try:
            write_dependencies()
            interval = dynamic_config.get("dependency_visualizer.interval_seconds", 3600)
            await asyncio.sleep(interval)
        except asyncio.CancelledError:
            return
        except Exception:
            log.exception("visualizer_loop error")
            await asyncio.sleep(interval)


if __name__ == "__main__":
    p = write_dependencies()
    print(f"written: {p}")
    print(p.read_text(encoding="utf-8")[:2000])
