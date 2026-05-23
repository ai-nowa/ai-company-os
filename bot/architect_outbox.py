"""Architect (Claude) が Discord 投稿要求をファイル経由で渡すキュー。

dispatcher の main_client が定期的に監視して、投稿後にファイル削除する。
これにより、dispatcher 動作中でも token 衝突なしで Architect が投稿できる。
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Optional

from .config import BASE_DIR, now_jst_iso

OUTBOX_DIR = BASE_DIR / "company" / ".architect_outbox"


def submit_post(
    channel: str,
    content: str,
    label: str = "",
    dispatch_to: Optional[list[str]] = None,
) -> Path:
    """Discord 投稿要求を提出。dispatcher が10秒以内に拾って投稿する。

    Args:
        channel: 投稿先チャンネル名（部分一致）
        content: 投稿内容
        label: ファイル名に使う短いラベル（オプション）
        dispatch_to: 投稿後に同じ内容で直接起動する社員ID（オプション）
    """
    OUTBOX_DIR.mkdir(parents=True, exist_ok=True)
    stamp = now_jst_iso().replace(":", "-").replace("+", "_")
    safe_label = ("_" + label) if label else ""
    fname = f"post_{stamp}{safe_label}.json"
    path = OUTBOX_DIR / fname
    tmp_path = OUTBOX_DIR / f".{fname}.tmp"
    tmp_path.write_text(
        json.dumps(
            {
                "channel": channel,
                "content": content,
                "dispatch_to": dispatch_to or [],
                "created_at": now_jst_iso(),
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    os.replace(tmp_path, path)
    return path


def pending_count() -> int:
    if not OUTBOX_DIR.exists():
        return 0
    return len(list(OUTBOX_DIR.glob("post_*.json")))
