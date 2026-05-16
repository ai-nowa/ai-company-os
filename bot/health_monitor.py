"""会社健康レポート生成。
discord_log/*.jsonl と outbox/ を集計し、health_report.md を更新する。
Phase 3 で文化指標の本実装（ジニ係数の精緻化、無視発言の検知など）を進める。
"""
from __future__ import annotations

import json
from collections import Counter
from datetime import datetime
from pathlib import Path

from .config import COMPANY_DIR, EMPLOYEES, EMPLOYEES_DIR, JST, now_jst_iso


def _gini(values: list[int]) -> float:
    if not values or sum(values) == 0:
        return 0.0
    sorted_v = sorted(values)
    n = len(sorted_v)
    cum = sum((i + 1) * v for i, v in enumerate(sorted_v))
    return (2 * cum / (n * sum(sorted_v))) - (n + 1) / n


def aggregate_today() -> dict:
    today = datetime.now(JST).date().isoformat()
    discord_log_dir = COMPANY_DIR / "discord_log"
    utterance_counts: Counter[str] = Counter()
    thanks_count = 0
    moyamoya_count = 0
    total_messages = 0
    unanswered: list[str] = []

    if discord_log_dir.exists():
        for f in discord_log_dir.glob("*.jsonl"):
            for line in f.read_text(encoding="utf-8").splitlines():
                try:
                    ev = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if not ev.get("ts", "").startswith(today):
                    continue
                total_messages += 1
                author = ev.get("author", "unknown")
                utterance_counts[author] += 1
                text = ev.get("text", "")
                if "ありがとう" in text or "👏" in text:
                    thanks_count += 1
                if "モヤモヤ" in text or "🧯" in text:
                    moyamoya_count += 1

    deliverables = sum(
        len([p for p in (EMPLOYEES_DIR / emp / "outbox").glob("*") if p.is_file() and p.name != ".keep"])
        for emp in EMPLOYEES.keys()
    )

    return {
        "date": today,
        "total_messages": total_messages,
        "utterance_counts": dict(utterance_counts),
        "gini": round(_gini(list(utterance_counts.values())), 3),
        "thanks_count": thanks_count,
        "moyamoya_count": moyamoya_count,
        "deliverables": deliverables,
    }


def _judge_status(m: dict) -> tuple[str, list[str]]:
    notes: list[str] = []
    status = "🟢 健康"
    if m["gini"] > 0.55:
        status = "🟡 注意"
        notes.append(f"発言の偏り大: gini={m['gini']} (目標 ≤ 0.4)")
    if m["thanks_count"] == 0:
        notes.append("👏ありがとう投稿が0件")
    if m["moyamoya_count"] > 5:
        status = "🔴 警告"
        notes.append("🧯モヤモヤ件数が多い")
    if m["total_messages"] < 20:
        notes.append(f"全体の会話量が少ない ({m['total_messages']}件)")
    return status, notes


def write_health_report() -> Path:
    m = aggregate_today()
    status, notes = _judge_status(m)

    md = [
        f"# 会社健康レポート {m['date']}",
        "",
        "## サマリー",
        f"- 状態: {status}",
        "- 一言: （ハルのコメント待ち）",
        "",
        "## 指標",
        f"- 総メッセージ数: {m['total_messages']}",
        f"- 発言ジニ係数: {m['gini']} (目標 ≤ 0.4)",
        f"- 👏ありがとう投稿: {m['thanks_count']}",
        f"- 🧯モヤモヤ件数: {m['moyamoya_count']}",
        f"- 📦成果物（outbox合計）: {m['deliverables']}",
        "",
        "## 発言量内訳",
    ]
    if m["utterance_counts"]:
        for author, count in sorted(m["utterance_counts"].items(), key=lambda x: -x[1]):
            md.append(f"- {author}: {count}")
    else:
        md.append("- （データなし）")
    if notes:
        md += ["", "## 注意点"] + [f"- {n}" for n in notes]
    md += ["", f"_生成: {now_jst_iso()}_"]

    path = COMPANY_DIR / "health_report.md"
    path.write_text("\n".join(md) + "\n", encoding="utf-8")
    return path


if __name__ == "__main__":
    p = write_health_report()
    print(f"Written: {p}")
