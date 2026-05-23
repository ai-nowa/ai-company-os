"""メンションレート制限モジュール。

仕様:
- 未知ユーザー（観察者ロール）: 1分3メンション まで
- 同一ユーザー: 1時間30メンション まで
- 超過 → 呼び出し元が無視 + DM 警告
- 9社員 bot は dispatcher 側で除外済み（ここでは処理しない）
- 履歴: company/.mention_rate.jsonl
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
MENTION_RATE_PATH = REPO_ROOT / "company" / ".mention_rate.jsonl"
JST = timezone(timedelta(hours=9))

OBSERVER_PER_MIN = 3
USER_PER_HOUR = 30


def _load_recent_sum(user_id: str, within_seconds: int) -> int:
    """直近 within_seconds 秒以内の user_id のメンション合計数を返す。"""
    if not MENTION_RATE_PATH.exists():
        return 0
    cutoff = datetime.now(JST) - timedelta(seconds=within_seconds)
    total = 0
    for line in MENTION_RATE_PATH.read_text(encoding="utf-8").splitlines():
        try:
            entry = json.loads(line)
            if entry.get("user_id") != user_id:
                continue
            ts = datetime.fromisoformat(entry["ts"])
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=JST)
            if ts >= cutoff:
                total += entry.get("mention_count", 1)
        except Exception:
            continue
    return total


def _record(user_id: str, channel_id: int, mention_count: int) -> None:
    """メンション実行を記録する。"""
    MENTION_RATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "ts": datetime.now(JST).isoformat(),
        "user_id": user_id,
        "channel_id": channel_id,
        "mention_count": mention_count,
    }
    with MENTION_RATE_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def check_and_record(
    user_id: str,
    channel_id: int,
    mention_count: int = 1,
    is_observer: bool = True,
) -> tuple[bool, str]:
    """レート制限チェックを行い、通過した場合は記録する。

    Returns:
        (allowed, reason) — allowed=False のとき reason に理由文字列
    """
    if is_observer:
        recent_1min = _load_recent_sum(user_id, 60)
        if recent_1min + mention_count > OBSERVER_PER_MIN:
            return (
                False,
                f"observer_rate_limit: 1分{OBSERVER_PER_MIN}件まで "
                f"(直近={recent_1min}, 今回={mention_count})",
            )

    recent_1h = _load_recent_sum(user_id, 3600)
    if recent_1h + mention_count > USER_PER_HOUR:
        return (
            False,
            f"hourly_rate_limit: 1時間{USER_PER_HOUR}件まで "
            f"(直近={recent_1h}, 今回={mention_count})",
        )

    _record(user_id, channel_id, mention_count)
    return True, "ok"
