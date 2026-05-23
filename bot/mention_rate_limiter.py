"""メンションレート制限モジュール（観察者ブロック後の二重防御）。

dispatcher の観察者ブロック層 (DISCORD_OWNER_USER_ID) が
Claude CLI 起動を完全に遮断したので、本モジュールの役割は変わった:

1. 観察者の👀 reaction 連打防止（reaction すら付けず無視）
   - 1 ユーザー 1 分 10 reaction まで
   - 履歴: company/.observer_reaction.jsonl

2. 9 社員 bot 同士のメンションチェーン暴走防止（clip）
   - 同一 emp_id が 1 時間に 20 メンション以上送ったら超過分を clip
   - 履歴: company/.employee_mention_burst.jsonl

オーナー（いくと）はどちらの制限も適用されない。
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
OBSERVER_REACTION_PATH = REPO_ROOT / "company" / ".observer_reaction.jsonl"
EMPLOYEE_MENTION_PATH = REPO_ROOT / "company" / ".employee_mention_burst.jsonl"
JST = timezone(timedelta(hours=9))

OBSERVER_REACTION_PER_MIN = 10
EMPLOYEE_MENTION_PER_HOUR = 20


def _count_recent(path: Path, key_field: str, key_value: str, within_seconds: int) -> int:
    """直近 within_seconds 秒以内の指定 key の count 合計を返す。"""
    if not path.exists():
        return 0
    cutoff = datetime.now(JST) - timedelta(seconds=within_seconds)
    total = 0
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            entry = json.loads(line)
            if entry.get(key_field) != key_value:
                continue
            ts = datetime.fromisoformat(entry["ts"])
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=JST)
            if ts >= cutoff:
                total += entry.get("count", 1)
        except Exception:
            continue
    return total


def _append_record(path: Path, entry: dict) -> None:
    """JSONL に 1 行追記する。古いエントリを定期的に刈り込む（48h 超は削除）。"""
    path.parent.mkdir(parents=True, exist_ok=True)
    cutoff = datetime.now(JST) - timedelta(hours=48)
    if path.exists():
        lines = path.read_text(encoding="utf-8").splitlines()
        kept = []
        for line in lines:
            try:
                e = json.loads(line)
                ts = datetime.fromisoformat(e["ts"])
                if ts.tzinfo is None:
                    ts = ts.replace(tzinfo=JST)
                if ts >= cutoff:
                    kept.append(line)
            except Exception:
                continue
        if len(kept) < len(lines):
            path.write_text("\n".join(kept) + ("\n" if kept else ""), encoding="utf-8")
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def should_react_to_observer(user_id: str) -> bool:
    """観察者に👀 reaction を付けるべきか判定。直近1分の reaction 数で判断。

    通過時のみ履歴に記録する（弾いた回数は記録しない）。
    """
    recent = _count_recent(OBSERVER_REACTION_PATH, "user_id", user_id, 60)
    if recent >= OBSERVER_REACTION_PER_MIN:
        return False
    _append_record(OBSERVER_REACTION_PATH, {
        "ts": datetime.now(JST).isoformat(),
        "user_id": user_id,
        "count": 1,
    })
    return True


def clip_employee_mentions(emp_id: str, targets: list[str]) -> tuple[list[str], int]:
    """社員間メンションを 1 時間 20 件に clip する。

    超過分を切り落とした targets と、削った件数を返す。
    通過した分のみ履歴に記録する。
    """
    if not targets:
        return targets, 0
    recent = _count_recent(EMPLOYEE_MENTION_PATH, "emp_id", emp_id, 3600)
    remaining = EMPLOYEE_MENTION_PER_HOUR - recent
    if remaining <= 0:
        return [], len(targets)
    if len(targets) <= remaining:
        kept = targets
        clipped = 0
    else:
        kept = targets[:remaining]
        clipped = len(targets) - remaining
    _append_record(EMPLOYEE_MENTION_PATH, {
        "ts": datetime.now(JST).isoformat(),
        "emp_id": emp_id,
        "count": len(kept),
    })
    return kept, clipped
