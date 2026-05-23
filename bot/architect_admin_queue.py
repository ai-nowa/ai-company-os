"""Architect (Claude) が Discord 管理操作（チャンネル作成・招待リンク・ロール権限変更）をファイル経由で依頼するキュー。

dispatcher の main_client が定期的に監視して、操作後に結果ファイルを残す。
これにより、dispatcher を停止せずに管理操作を実行できる（architect_outbox の管理操作版）。

サポートする op:
- create_channel: テキストチャンネル作成
- create_invite: 招待リンク作成
- update_everyone_permission: @everyone のチャンネル権限変更
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Optional

from .config import BASE_DIR, now_jst_iso

ADMIN_QUEUE_DIR = BASE_DIR / "company" / ".architect_admin_queue"


def submit_admin_op(op: str, params: dict[str, Any], label: str = "") -> Path:
    """管理操作リクエストをキューに投入。dispatcher が 10 秒以内に拾って実行する。

    Args:
        op: 操作名（create_channel / create_invite / update_everyone_permission）
        params: 操作のパラメータ（op ごとに違う）
        label: ファイル名に使う短いラベル（オプション）

    Returns:
        作成したリクエストファイルのパス。結果は同じ名前の .result.json に書かれる。
    """
    ADMIN_QUEUE_DIR.mkdir(parents=True, exist_ok=True)
    stamp = now_jst_iso().replace(":", "-").replace("+", "_")
    safe_label = ("_" + label) if label else ""
    fname = f"admin_{stamp}_{op}{safe_label}.json"
    path = ADMIN_QUEUE_DIR / fname
    tmp_path = ADMIN_QUEUE_DIR / f".{fname}.tmp"
    tmp_path.write_text(
        json.dumps(
            {"op": op, "params": params, "created_at": now_jst_iso()},
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    os.replace(tmp_path, path)
    return path


def read_result(request_path: Path, timeout_s: int = 30) -> Optional[dict[str, Any]]:
    """結果ファイル（.result.json）を読む。なければ None。timeout_s で待機。"""
    import time
    result_path = request_path.with_suffix(".result.json")
    start = time.time()
    while time.time() - start < timeout_s:
        if result_path.exists():
            return json.loads(result_path.read_text(encoding="utf-8"))
        time.sleep(0.5)
    return None
