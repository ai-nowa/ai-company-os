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
            "enabled": True,
            "stale_threshold_hours": 24,
        },
        "token_pace": {
            "alert_prompt_chars": 50000,
        },
        "llm_circuit": {
            "enabled": True,
            "claude_cooldown_minutes": 15,
            "claude_failure_threshold": 2,
            "claude_failure_window_minutes": 10,
        },
        "external_check": {
            "enabled": True,
            "interval_seconds": 1800,
            "request_timeout": 10,
        },
        "architect_observer": {
            "enabled": True,
            "check_interval_seconds": 12600,
            "initial_delay_seconds": 1800,
            "keyword_loop_threshold": 30,
            "silent_hours": 2,
            "token_overheat_threshold": 60000,
            "watched_keywords": [
                "AdSense", "Public", "Private", "公開判断", "監査",
                "法務", "ブロッカー", "撤退", "Zenn", "404",
            ],
        },
        "architect_outbox": {
            "dispatch_timeout_seconds": 900,
            "max_dispatch_targets": 2,
        },
        "architect": {
            "model": "claude-opus-4-7",
            "modes": {
                "manual": {
                    "effort": "xhigh",
                    "use_resume": True,
                    "max_output_tokens": 4000,
                    "max_response_chars": 5000,
                    "timeout_seconds": 900,
                },
                "auto": {
                    "effort": "high",
                    "use_resume": False,
                    "max_output_tokens": 1200,
                    "max_response_chars": 1200,
                    "timeout_seconds": 300,
                },
                "observer": {
                    "effort": "high",
                    "use_resume": False,
                    "max_output_tokens": 1400,
                    "max_response_chars": 1600,
                    "timeout_seconds": 360,
                },
                "incident": {
                    "effort": "xhigh",
                    "use_resume": False,
                    "max_output_tokens": 1600,
                    "max_response_chars": 1800,
                    "timeout_seconds": 360,
                },
                "broadcast": {
                    "effort": "high",
                    "use_resume": False,
                    "max_output_tokens": 1800,
                    "max_response_chars": 2200,
                    "timeout_seconds": 360,
                },
            },
            "auto_response": {
                "enabled": True,
                "window_seconds": 1800,
                "max_calls": 2,
                "allowed_employee_ids": [
                    "arima_reiji", "saegusa_mio", "shirase_kai", "kagura_aoi",
                ],
                "critical_keywords": [
                    "P0", "critical", "incident", "障害", "停止", "再起動ループ", "dispatcher",
                    "セキュリティ", "security", "流出", "漏洩", "APIキー", "api key", "secret",
                    "token", "権限", "admin", "管理者", "invite", "招待", "認証", "OAuth",
                    "決済", "支払い", "請求", "返金", "契約", "法務", "本番", "deploy",
                    "公開可否", "公開判断", "削除", "delete", "リミット", "usage cap",
                    "トークン過熱", "自己改修", "外部投稿",
                ],
            },
        },
        "admin_queue": {
            "enabled": False,
            "allowed_ops": ["create_channel", "create_invite", "update_everyone_permission"],
            "default_invite_max_age": 86400,
            "default_invite_max_uses": 1,
        },
        "outbox_organizer": {
            "enabled": False,
            "interval_seconds": 3600,
        },
        "auto_commit": {
            "enabled": False,
            "interval_seconds": 3600,
        },
        "dependency_visualizer": {
            "enabled": True,
            "interval_seconds": 3600,
        },
        "dashboard_writer": {
            "enabled": True,
            "interval_seconds": 900,
        },
        "self_improvement_loop": {
            "check_interval_seconds": 3600,
            "max_triggers_per_cycle": 2,
        },
        "mention_chain": {
            "max_depth": 4,
            "max_chain_calls": 6,
            "max_initial_targets": 6,
            "max_mentions_per_response": 2,
            "heartbeat_chain_calls": 1,
            "architect_chain_calls": 2,
        },
        "model_policy": {
            "enabled": True,
            "ceo_always_xhigh": True,
            "high_judgment_employees": [
                "saegusa_mio", "shirase_kai", "asakura_noa", "kuroba_yuu", "kagura_aoi",
            ],
            "creative_high_employees": ["hoshino_ritsu", "morinaga_haru", "hinata_nagi"],
            "models": {
                "codex": {
                    "ceo": "gpt-5.5",
                    "default": "gpt-5.5",
                },
                "claude": {
                    "default": "sonnet",
                    "micro": "sonnet",
                    "executive": "opus",
                },
            },
            "fallbacks": {
                "claude": {
                    "opus": "sonnet",
                    "sonnet": "haiku",
                    "haiku": None,
                },
            },
            "efforts": {
                "codex": {
                    "micro": "low",
                    "routine": "medium",
                    "judgment_routine": "high",
                    "business_routine": "high",
                    "creative_routine": "high",
                    "conversation": "high",
                    "deep_work": "high",
                    "risk_review": "xhigh",
                    "executive": "xhigh",
                    "crisis": "xhigh",
                },
                "claude": {
                    "micro": "low",
                    "routine": "medium",
                    "judgment_routine": "high",
                    "business_routine": "high",
                    "creative_routine": "high",
                    "conversation": "high",
                    "deep_work": "high",
                    "risk_review": "xhigh",
                    "executive": "xhigh",
                    "crisis": "max",
                },
            },
            "max_output_tokens": {
                "micro": 700,
                "routine": 1600,
                "work": 6000,
                "executive": 6000,
            },
            "keywords": {
                "decision": [
                    "公開可否", "公開する", "リリース", "投資判断", "最終承認",
                    "炎上", "監査判定", "重要判断", "P0", "[important]", "[critical]",
                    "本番投入", "契約", "支出", "違反", "価格", "撤退", "採用",
                ],
                "crisis": [
                    "障害", "停止", "流出", "炎上", "返金", "法務", "契約解除", "重大",
                    "critical", "[critical]", "p0", "security", "incident",
                ],
                "risk": [
                    "権限", "認証", "OAuth", "APIキー", "api key", "token", "secret", "secrets",
                    "password", "パスワード", ".env", "credential", "credentials", "秘密",
                    "個人情報", "PII", "プライバシー", "公開範囲", "public", "private",
                    "決済", "支払い", "請求", "課金", "返金", "webhook", "署名検証",
                    "Cloudflare", "R2", "DNS", "admin", "管理者", "invite", "招待",
                    "削除", "delete", "archive", "自動化", "外部投稿", "本番", "deploy",
                    "production", "公開", "セキュリティ", "運用リスク", "監査",
                ],
                "revenue": [
                    "収益", "売上", "販売", "購入", "導入意向", "価格", "CVR",
                    "Revenue", "experiment", "success_signal", "north_star",
                ],
                "creative": [
                    "[IDEA]", "アイデア", "企画", "台本", "コンセプト", "仮説", "新規事業",
                    "戦略", "ブランド", "視聴者", "見学者", "雑談", "発見", "改善案",
                    "ストーリー", "動画", "記事", "コピー", "サムネ", "導線",
                ],
            },
        },
    }


def _deep_merge(base: dict, override: dict) -> dict:
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(base.get(key), dict):
            _deep_merge(base[key], value)
        else:
            base[key] = value
    return base


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
    # default を再帰マージ（ユーザーが未定義キーは default 値で補完）
    return _deep_merge(_defaults(), loaded)


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
