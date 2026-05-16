"""社員のチャンネル/スレッドアクセス権管理。

Teams 的な「自分が参加している場所だけ存在を認識する」を実現するための制御層。
社員起動時に「アクセス可能な場所のリスト」を system prompt に注入する。

デフォルトチャンネルは config.EMPLOYEES の default_channels（部分文字列マッチ）。
スレッドは thread_registry に従う。
"""
from __future__ import annotations

from typing import Optional

from .config import EMPLOYEES
from . import thread_registry

# 「all」キーワード = 全チャンネル閲覧可能（People担当ハル用）
SPECIAL_ALL = "all"


def employee_default_channels(employee_id: str) -> list[str]:
    """その社員がデフォルトで参加しているチャンネル名（部分マッチパターン）"""
    info = EMPLOYEES.get(employee_id, {})
    return info.get("default_channels", [])


def can_access_channel(employee_id: str, channel_name: str) -> bool:
    """社員がそのチャンネル名を見られるか"""
    patterns = employee_default_channels(employee_id)
    if SPECIAL_ALL in patterns:
        return True
    return any(p in channel_name for p in patterns if p != SPECIAL_ALL)


def accessible_channels(employee_id: str, all_channels: list[str]) -> list[str]:
    """与えられたチャンネル名リストから、この社員が見えるものだけ返す"""
    return [c for c in all_channels if can_access_channel(employee_id, c)]


def accessible_threads(employee_id: str) -> list[dict]:
    """この社員が参加しているアクティブスレッドの一覧"""
    return thread_registry.list_threads_for(employee_id, active_only=True)


def build_access_snippet(employee_id: str, all_channels: list[str]) -> str:
    """social prompt に注入する『アクセス可能な場所』ブロックを生成"""
    chans = accessible_channels(employee_id, all_channels)
    threads = accessible_threads(employee_id)

    lines = ["## あなたが今アクセスできる場所", ""]
    lines.append("### チャンネル")
    if chans:
        for c in chans:
            lines.append(f"- {c}")
    else:
        lines.append("- （なし）")
    lines.append("")
    lines.append("### スレッド（参加者として招待されている）")
    if threads:
        for t in threads:
            participants = ", ".join(t["participants"])
            tag = "🔒 プライベート" if t.get("private") else "公開"
            lines.append(f"- 「{t['name']}」({tag}) — 参加者: {participants}")
    else:
        lines.append("- （現在参加中のスレッドなし）")
    lines.append("")
    lines.append(
        "**重要**: 上記以外のチャンネル・スレッドは存在を知りません。"
        "もし自分が必要な場所に参加していないと感じたら、関係者にメンションで呼んでもらうか、"
        "自分でスレッドを新規作成（メタタグ `thread=...`）してください。"
    )
    return "\n".join(lines)
