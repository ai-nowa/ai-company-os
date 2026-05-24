"""Policy helpers for Architect (Opus) intervention paths.

Architect is intentionally a scarce external-auditor path. Manual founder
calls stay powerful, while automatic Discord triggers must be gated so the
company does not turn every mention into an Opus meeting.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from . import dynamic_config


DEFAULT_CRITICAL_KEYWORDS = [
    "P0", "critical", "incident", "障害", "停止", "再起動ループ", "dispatcher",
    "セキュリティ", "security", "流出", "漏洩", "APIキー", "api key", "secret",
    "token", "権限", "admin", "管理者", "invite", "招待", "認証", "OAuth",
    "決済", "支払い", "請求", "返金", "契約", "法務", "本番", "deploy",
    "公開可否", "公開判断", "削除", "delete", "リミット", "usage cap",
    "トークン過熱", "自己改修", "外部投稿",
]

DEFAULT_ALLOWED_EMPLOYEES = [
    "arima_reiji",
    "saegusa_mio",
    "shirase_kai",
    "kagura_aoi",
]

KNOWN_ARCHITECT_MODES = {"manual", "auto", "observer", "incident", "broadcast"}


@dataclass(frozen=True)
class ArchitectModeSettings:
    mode: str
    model: str
    effort: str
    use_resume: bool
    max_output_tokens: int
    max_response_chars: int
    timeout_seconds: int


@dataclass(frozen=True)
class AutoArchitectDecision:
    allowed: bool
    reason: str


def _get(path: str, default: Any) -> Any:
    return dynamic_config.get(path, default)


def _as_list(value: Any, default: list[str]) -> list[str]:
    if isinstance(value, list):
        return [str(v) for v in value if str(v).strip()]
    return default


def _as_bool(value: Any, default: bool) -> bool:
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    if value is None:
        return default
    return bool(value)


def _as_int(value: Any, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _contains_any(text: str, words: list[str]) -> bool:
    lower = text.lower()
    return any(word.lower() in lower for word in words)


def architect_mode_settings(mode: str) -> ArchitectModeSettings:
    mode = mode if mode in KNOWN_ARCHITECT_MODES else "manual"
    defaults = {
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
    }[mode]
    return ArchitectModeSettings(
        mode=mode,
        model=str(_get("architect.model", "claude-opus-4-7")),
        effort=str(_get(f"architect.modes.{mode}.effort", defaults["effort"])),
        use_resume=_as_bool(_get(f"architect.modes.{mode}.use_resume", defaults["use_resume"]), defaults["use_resume"]),
        max_output_tokens=_as_int(
            _get(f"architect.modes.{mode}.max_output_tokens", defaults["max_output_tokens"]),
            defaults["max_output_tokens"],
        ),
        max_response_chars=_as_int(
            _get(f"architect.modes.{mode}.max_response_chars", defaults["max_response_chars"]),
            defaults["max_response_chars"],
        ),
        timeout_seconds=_as_int(
            _get(f"architect.modes.{mode}.timeout_seconds", defaults["timeout_seconds"]),
            defaults["timeout_seconds"],
        ),
    )


def auto_response_window_seconds() -> int:
    return _as_int(_get("architect.auto_response.window_seconds", 1800), 1800)


def auto_response_max_calls() -> int:
    return _as_int(_get("architect.auto_response.max_calls", 2), 2)


def should_auto_architect_respond(text: str, employee_id: str | None) -> AutoArchitectDecision:
    if not _as_bool(_get("architect.auto_response.enabled", True), True):
        return AutoArchitectDecision(False, "architect_auto_disabled")

    critical_keywords = _as_list(
        _get("architect.auto_response.critical_keywords", DEFAULT_CRITICAL_KEYWORDS),
        DEFAULT_CRITICAL_KEYWORDS,
    )
    if _contains_any(text, critical_keywords):
        return AutoArchitectDecision(True, "critical_keyword")

    allowed_employees = set(_as_list(
        _get("architect.auto_response.allowed_employee_ids", DEFAULT_ALLOWED_EMPLOYEES),
        DEFAULT_ALLOWED_EMPLOYEES,
    ))
    if employee_id in allowed_employees:
        return AutoArchitectDecision(True, "allowed_employee")

    return AutoArchitectDecision(False, "noncritical_employee_architect_mention")
