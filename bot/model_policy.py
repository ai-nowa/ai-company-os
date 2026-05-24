"""Model and reasoning-effort routing for AI NOWA employees.

The policy is intentionally explicit. Low effort can create expensive rework,
while high effort everywhere burns limits and slows the company down. This
module centralizes the tradeoff so it can be inspected, tested, and tuned.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from .config import EMPLOYEES
from . import dynamic_config

RUN_MODES = {"micro", "routine", "work", "executive"}
FRESH_ROUTINE_SENDERS = {"self_loop", "heartbeat", "daily_loop", "watchdog"}

DEFAULT_DECISION_KEYWORDS = [
    "公開可否", "公開する", "リリース", "投資判断", "最終承認",
    "炎上", "監査判定", "重要判断", "P0", "[important]", "[critical]",
    "本番投入", "契約", "支出", "違反", "価格", "撤退", "採用",
]
DEFAULT_CRISIS_KEYWORDS = [
    "障害", "停止", "流出", "炎上", "返金", "法務", "契約解除", "重大",
    "critical", "[critical]", "p0", "security", "incident",
]
DEFAULT_RISK_KEYWORDS = [
    "権限", "認証", "OAuth", "APIキー", "api key", "token", "secret", "secrets",
    "password", "パスワード", ".env", "credential", "credentials", "秘密",
    "個人情報", "PII", "プライバシー", "公開範囲", "public", "private",
    "決済", "支払い", "請求", "課金", "返金", "webhook", "署名検証",
    "Cloudflare", "R2", "DNS", "admin", "管理者", "invite", "招待",
    "削除", "delete", "archive", "自動化", "外部投稿", "本番", "deploy",
    "production", "公開", "セキュリティ", "運用リスク", "監査",
]
DEFAULT_REVENUE_KEYWORDS = [
    "収益", "売上", "販売", "購入", "導入意向", "価格", "CVR",
    "Revenue", "experiment", "success_signal", "north_star",
]
DEFAULT_CREATIVE_KEYWORDS = [
    "[IDEA]", "アイデア", "企画", "台本", "コンセプト", "仮説", "新規事業",
    "戦略", "ブランド", "視聴者", "見学者", "雑談", "発見", "改善案",
    "ストーリー", "動画", "記事", "コピー", "サムネ", "導線",
]

EFFORT_ORDER = ["none", "low", "medium", "high", "xhigh", "max"]
EFFORT_RANK = {effort: idx for idx, effort in enumerate(EFFORT_ORDER)}
CLAUDE_FAMILY_EFFORTS = {
    "opus": {"low", "medium", "high", "xhigh", "max"},
    "sonnet": {"low", "medium", "high", "max"},
    "haiku": {"low"},
}


@dataclass(frozen=True)
class ModelRoute:
    backend: str
    model: str
    effort: str
    tier: str
    reason: str
    fallback_model: Optional[str] = None
    max_output_tokens: Optional[int] = None
    escalated: bool = False


def _get(path: str, default: Any) -> Any:
    return dynamic_config.get(path, default)


def _as_list(value: Any, default: list[str]) -> list[str]:
    if isinstance(value, list):
        return [str(v) for v in value if str(v).strip()]
    return default


def _contains_any(text: str, words: list[str]) -> bool:
    lower = text.lower()
    return any(str(word).lower() in lower for word in words)


def is_real_conversation(sender: str) -> bool:
    return sender not in FRESH_ROUTINE_SENDERS


def decision_keywords() -> list[str]:
    return _as_list(_get("model_policy.keywords.decision", DEFAULT_DECISION_KEYWORDS), DEFAULT_DECISION_KEYWORDS)


def crisis_keywords() -> list[str]:
    return _as_list(_get("model_policy.keywords.crisis", DEFAULT_CRISIS_KEYWORDS), DEFAULT_CRISIS_KEYWORDS)


def risk_keywords() -> list[str]:
    return _as_list(_get("model_policy.keywords.risk", DEFAULT_RISK_KEYWORDS), DEFAULT_RISK_KEYWORDS)


def revenue_keywords() -> list[str]:
    return _as_list(_get("model_policy.keywords.revenue", DEFAULT_REVENUE_KEYWORDS), DEFAULT_REVENUE_KEYWORDS)


def creative_keywords() -> list[str]:
    return _as_list(_get("model_policy.keywords.creative", DEFAULT_CREATIVE_KEYWORDS), DEFAULT_CREATIVE_KEYWORDS)


def needs_executive_model(text: str) -> bool:
    return (
        _contains_any(text, decision_keywords())
        or _contains_any(text, crisis_keywords())
        or _contains_any(text, risk_keywords())
    )


def needs_crisis_effort(text: str) -> bool:
    return _contains_any(text, crisis_keywords())


def _claude_family(model: str) -> str:
    lowered = model.lower()
    if "opus" in lowered:
        return "opus"
    if "haiku" in lowered:
        return "haiku"
    return "sonnet"


def _clamp_claude_effort(model: str, effort: str) -> str:
    family = _claude_family(model)
    supported = CLAUDE_FAMILY_EFFORTS.get(family, CLAUDE_FAMILY_EFFORTS["sonnet"])
    if effort in supported:
        return effort
    requested_rank = EFFORT_RANK.get(effort, EFFORT_RANK["medium"])
    candidates = [e for e in EFFORT_ORDER if e in supported and EFFORT_RANK[e] <= requested_rank]
    return candidates[-1] if candidates else next(iter(supported))


def _mode_tier(mode: str, sender: str, employee_id: str, text: str) -> tuple[str, list[str]]:
    reasons: list[str] = []
    high_judgment = set(_get("model_policy.high_judgment_employees", [
        "saegusa_mio", "shirase_kai", "asakura_noa", "kuroba_yuu", "kagura_aoi",
    ]))
    creative_high = set(_get("model_policy.creative_high_employees", [
        "hoshino_ritsu", "morinaga_haru", "hinata_nagi",
    ]))

    if needs_crisis_effort(text):
        return "crisis", ["crisis keyword"]
    if mode == "executive" or _contains_any(text, decision_keywords()):
        return "executive", ["executive/decision"]
    if _contains_any(text, risk_keywords()):
        return "risk_review", ["risk keyword"]
    if mode == "work":
        return "deep_work", ["work mode"]
    if mode == "micro":
        return "micro", ["micro mode"]
    if _contains_any(text, revenue_keywords()):
        reasons.append("revenue keyword")
        if employee_id in high_judgment:
            return "business_routine", reasons
    if _contains_any(text, creative_keywords()):
        reasons.append("creative/strategy keyword")
        if employee_id in creative_high or employee_id in high_judgment:
            return "creative_routine", reasons
    if is_real_conversation(sender):
        return "conversation", reasons + ["real conversation"]
    if employee_id in high_judgment:
        return "judgment_routine", reasons + ["high-judgment role"]
    return "routine", reasons or ["routine"]


def _effort_from_matrix(backend: str, tier: str, default: str) -> str:
    return str(_get(f"model_policy.efforts.{backend}.{tier}", default))


def _mode_output_cap(mode: str) -> Optional[int]:
    value = _get(f"model_policy.max_output_tokens.{mode}", None)
    try:
        return int(value) if value else None
    except (TypeError, ValueError):
        return None


def _claude_model_for(tier: str, model_override: Optional[str], employee_id: str) -> str:
    if model_override:
        return model_override
    employee_override = _get(f"model_policy.employee_model_overrides.{employee_id}", None)
    if employee_override:
        return str(employee_override)
    if tier in {"crisis", "risk_review", "executive"}:
        return str(_get("model_policy.models.claude.executive", "opus"))
    if tier == "micro":
        return str(_get("model_policy.models.claude.micro", "sonnet"))
    return str(_get("model_policy.models.claude.default", EMPLOYEES[employee_id].get("model", "sonnet")))


def _claude_fallback_for(model: str) -> Optional[str]:
    family = _claude_family(model)
    fallback = _get(f"model_policy.fallbacks.claude.{family}", None)
    return str(fallback) if fallback else None


def _codex_model_for(employee_id: str) -> str:
    if employee_id == "arima_reiji":
        return str(_get("model_policy.models.codex.ceo", EMPLOYEES[employee_id].get("model", "gpt-5.5")))
    return str(_get("model_policy.models.codex.default", EMPLOYEES[employee_id].get("model", "gpt-5.5")))


def resolve_model_route(
    employee_id: str,
    mode: str,
    sender: str,
    user_message: str,
    run_reason: str,
    model_override: Optional[str] = None,
) -> ModelRoute:
    backend = EMPLOYEES[employee_id]["backend"]
    is_self_loop_boilerplate = (
        sender == "self_loop"
        and "あなた自身の時間です" in user_message
        and "## まずstate_digestを見る" in user_message
    )
    if is_self_loop_boilerplate or sender in {"heartbeat", "watchdog"}:
        # self_loop/heartbeat の user_message は運用ルール全文を含むため、
        # 「経営判断」「権限」などの注意書きだけで Opus/xhigh に誤昇格させない。
        text = run_reason
    else:
        text = f"{run_reason}\n{user_message}"
    tier, reasons = _mode_tier(mode, sender, employee_id, text)

    if backend == "codex":
        model = _codex_model_for(employee_id)
        if employee_id == "arima_reiji" and bool(_get("model_policy.ceo_always_xhigh", True)):
            effort = "xhigh"
            reasons.append("CEO always xhigh")
        else:
            effort = _effort_from_matrix("codex", tier, "medium")
        return ModelRoute(
            backend=backend,
            model=model,
            effort=effort,
            tier=tier,
            reason=", ".join(reasons),
            max_output_tokens=_mode_output_cap(mode),
            escalated=tier in {"crisis", "risk_review", "executive"} or EFFORT_RANK.get(effort, 0) >= EFFORT_RANK["high"],
        )

    model = _claude_model_for(tier, model_override, employee_id)
    default_effort = {
        "crisis": "max",
        "risk_review": "xhigh",
        "executive": "xhigh",
        "deep_work": "high",
        "conversation": "high",
        "creative_routine": "high",
        "business_routine": "high",
        "judgment_routine": "high",
        "routine": "medium",
        "micro": "low",
    }.get(tier, "medium")
    effort = _effort_from_matrix("claude", tier, default_effort)
    effort = _clamp_claude_effort(model, effort)
    return ModelRoute(
        backend=backend,
        model=model,
        effort=effort,
        tier=tier,
        reason=", ".join(reasons),
        fallback_model=_claude_fallback_for(model),
        max_output_tokens=_mode_output_cap(mode),
        escalated=tier in {"crisis", "risk_review", "executive"} or _claude_family(model) == "opus",
    )
