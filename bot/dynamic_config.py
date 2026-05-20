"""動的設定モジュール。

目的: 閾値・間隔・キーワード等の「値変更だけ」で dispatcher 再起動が不要になるようにする。

仕組み:
- `company/dynamic_config.yaml` を真実のソースとする
- 初回 import 時にデフォルトを書き出す（既存設定があれば上書きしない）
- get(path) でドット区切りアクセス
- 5分キャッシュ。それを超えたら自動再読み込み
- yaml 編集 → 5分以内に全 watcher に伝わる（再起動不要）

これで動的にできるもの:
- 各 watcher の interval
- 各 watcher の閾値・キーワードリスト
- mention_chain の上限値

動的にできないもの（再起動必要）:
- 新しい watcher の追加
- 関数定義の変更
- system prompt の構造変更
"""
from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Any

import yaml

from .config import BASE_DIR

log = logging.getLogger("dynamic_config")

CONFIG_PATH = BASE_DIR / "company" / "dynamic_config.yaml"
RELOAD_INTERVAL = 300  # 5分

_cache: dict = {}
_cache_loaded_at: float = 0.0


def _defaults() -> dict:
    return {
        "task_health": {
            "stale_threshold_hours": 24,
        },
        "token_pace": {
            "alert_prompt_chars": 50000,
        },
        "external_check": {
            "interval_seconds": 1800,
            "request_timeout": 10,
        },
        "architect_observer": {
            "check_interval_seconds": 12600,
            "keyword_loop_threshold": 30,
            "silent_hours": 2,
            "token_overheat_threshold": 60000,
            "watched_keywords": [
                "AdSense", "Public", "Private", "公開判断", "監査",
                "法務", "ブロッカー", "撤退", "Zenn", "404",
            ],
        },
        "outbox_organizer": {
            "interval_seconds": 3600,
        },
        "auto_commit": {
            "interval_seconds": 3600,
        },
        "dependency_visualizer": {
            "interval_seconds": 3600,
        },
        "dashboard_writer": {
            "interval_seconds": 900,
        },
        "mention_chain": {
            "max_depth": 4,
            "max_chain_calls": 6,
            "max_mentions_per_response": 2,
            "heartbeat_chain_calls": 1,
        },
    }


def _ensure_file() -> None:
    """初回起動時、設定ファイルが存在しないなら作成"""
    if CONFIG_PATH.exists():
        return
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    content = (
        "# AI NOWA 動的設定ファイル\n"
        "# 値を変更したら 5分以内に全 watcher に反映される（再起動不要）。\n"
        "# 構造変更（新キー追加・型変更）は dynamic_config.py の _defaults() も更新する。\n\n"
        + yaml.safe_dump(_defaults(), allow_unicode=True, sort_keys=False)
    )
    CONFIG_PATH.write_text(content, encoding="utf-8")
    log.info(f"created default config: {CONFIG_PATH}")


def _load_config() -> dict:
    _ensure_file()
    try:
        loaded = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8")) or {}
    except Exception:
        log.exception(f"failed to parse {CONFIG_PATH}, falling back to defaults")
        return _defaults()
    # default をマージ（ユーザーが未定義キーは default 値で補完）
    merged = _defaults()
    for k, v in loaded.items():
        if isinstance(v, dict) and isinstance(merged.get(k), dict):
            merged[k].update(v)
        else:
            merged[k] = v
    return merged


def _maybe_reload() -> None:
    global _cache, _cache_loaded_at
    now = time.time()
    if not _cache or (now - _cache_loaded_at) > RELOAD_INTERVAL:
        _cache = _load_config()
        _cache_loaded_at = now


def get(path: str, default: Any = None) -> Any:
    """ドット区切りで設定値を取得。

    例: get('task_health.stale_threshold_hours', 24)
    """
    _maybe_reload()
    cur: Any = _cache
    for key in path.split("."):
        if not isinstance(cur, dict) or key not in cur:
            return default
        cur = cur[key]
    return cur


def reload_now() -> None:
    """強制リロード（テスト用 or 手動）"""
    global _cache, _cache_loaded_at
    _cache = _load_config()
    _cache_loaded_at = time.time()


if __name__ == "__main__":
    # 単体テスト
    print(f"config path: {CONFIG_PATH}")
    print(f"exists: {CONFIG_PATH.exists()}")
    _ensure_file()
    reload_now()
    import json
    print(json.dumps(_cache, ensure_ascii=False, indent=2))
