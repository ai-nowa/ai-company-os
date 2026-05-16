"""スレッド参加者の永続管理。

各スレッドの thread_id → {name, channel_id, participants, private, created_at, status} を JSON で保存。
プライベートスレッドはいくとを自動招待する。
"""
from __future__ import annotations

import json
import threading
from typing import Optional

from .config import COMPANY_DIR, now_jst_iso

REGISTRY_PATH = COMPANY_DIR / "thread_registry.json"
_lock = threading.Lock()

OWNER_ID = "ikuto"  # いくと（人間 Co-Founder）


def _load() -> dict:
    if not REGISTRY_PATH.exists():
        return {"threads": {}}
    try:
        return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"threads": {}}


def _save(data: dict) -> None:
    REGISTRY_PATH.parent.mkdir(parents=True, exist_ok=True)
    REGISTRY_PATH.write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def register_thread(
    thread_id: int,
    name: str,
    channel_id: int,
    participants: list[str],
    private: bool = False,
    creator: Optional[str] = None,
) -> dict:
    """新規スレッドを登録。プライベートなら自動で owner を含める"""
    with _lock:
        data = _load()
        # 参加者集合（重複排除）
        members = set(participants)
        if creator:
            members.add(creator)
        if private:
            members.add(OWNER_ID)  # いくとを自動招待
        record = {
            "name": name,
            "channel_id": channel_id,
            "participants": sorted(members),
            "private": private,
            "creator": creator,
            "created_at": now_jst_iso(),
            "status": "active",
        }
        data["threads"][str(thread_id)] = record
        _save(data)
        return record


def get_thread(thread_id: int) -> Optional[dict]:
    data = _load()
    return data["threads"].get(str(thread_id))


def get_participants(thread_id: int) -> list[str]:
    rec = get_thread(thread_id)
    return rec["participants"] if rec else []


def is_participant(thread_id: int, employee_id: str) -> bool:
    return employee_id in get_participants(thread_id)


def add_participant(thread_id: int, employee_id: str) -> bool:
    """参加者を追加。既に参加していれば False、追加できれば True"""
    with _lock:
        data = _load()
        rec = data["threads"].get(str(thread_id))
        if not rec:
            return False
        if employee_id in rec["participants"]:
            return False
        rec["participants"].append(employee_id)
        rec["participants"].sort()
        _save(data)
        return True


def close_thread(thread_id: int) -> bool:
    with _lock:
        data = _load()
        rec = data["threads"].get(str(thread_id))
        if not rec:
            return False
        rec["status"] = "closed"
        rec["closed_at"] = now_jst_iso()
        _save(data)
        return True


def list_threads_for(employee_id: str, active_only: bool = True) -> list[dict]:
    """指定社員が参加中のスレッド一覧"""
    data = _load()
    out: list[dict] = []
    for tid, rec in data["threads"].items():
        if active_only and rec.get("status") != "active":
            continue
        if employee_id in rec["participants"]:
            out.append({"thread_id": tid, **rec})
    return out


def all_active_threads() -> list[dict]:
    data = _load()
    return [
        {"thread_id": tid, **rec}
        for tid, rec in data["threads"].items()
        if rec.get("status") == "active"
    ]


def find_active_thread_by_name(name: str, channel_id: Optional[int] = None) -> Optional[dict]:
    """指定名（および任意で同チャンネル）の active スレッドを返す（重複作成防止）"""
    data = _load()
    for tid, rec in data["threads"].items():
        if rec.get("status") != "active":
            continue
        if rec.get("name") != name:
            continue
        if channel_id is not None and rec.get("channel_id") != channel_id:
            continue
        return {"thread_id": tid, **rec}
    return None
