"""Owner request gate.

AI NOWA は「人間を動かさないための会社」なので、社員が安易に
`いくと依頼` へ公開・投稿・確認作業を投げるのを止める。
本当に人間しかできない認証/本人確認/契約系だけ、明示マーカー付きで通す。
"""
from __future__ import annotations

from dataclasses import dataclass, field

OWNER_REQUEST_MARKER = "[HUMAN_REQUIRED]"

OWNER_CHANNEL_MARKERS = ("いくと依頼", "📥")

HARD_HUMAN_KEYWORDS = (
    "OAuth",
    "認証",
    "ログイン",
    "2FA",
    "二段階",
    "本人確認",
    "身分証",
    "APIキー",
    "api key",
    "secret",
    "secrets",
    ".env",
    "credential",
    "credentials",
    "契約",
    "法務",
    "支払い",
    "決済",
    "請求",
    "返金",
    "銀行",
    "口座",
    "Stripe",
    "Lemon Squeezy",
    "Cloudflare",
    "DNS",
    "Google Cloud",
    "YouTube OAuth",
)

AUTH_FAILURE_KEYWORDS = (
    "失効",
    "期限切れ",
    "invalid",
    "expired",
    "refresh failed",
    "refresh_error",
    "再認証",
    "consent",
    "scope不足",
    "権限不足",
)


@dataclass
class OwnerRequestDecision:
    allowed: bool
    reason: str
    route: str = ""
    suggested_action: str = ""
    checks: list[str] = field(default_factory=list)
    fallback: str = ""


def is_owner_request_channel_name(channel_name: str) -> bool:
    return any(marker in channel_name for marker in OWNER_CHANNEL_MARKERS)


def _contains_hard_human_keyword(text: str) -> bool:
    lowered = text.lower()
    return any(keyword.lower() in lowered for keyword in HARD_HUMAN_KEYWORDS)


def _contains_auth_failure_keyword(text: str) -> bool:
    lowered = text.lower()
    return any(keyword.lower() in lowered for keyword in AUTH_FAILURE_KEYWORDS)


def evaluate_owner_request(text: str) -> OwnerRequestDecision:
    """Return whether a request is truly human-only and what to try first."""
    try:
        from .output_routes import route_preflight_for_text

        route = route_preflight_for_text(text)
    except Exception:
        route = {}

    route_id = str(route.get("route") or "")
    if route_id and route.get("available"):
        # Stale OAuth requests should not pass once the route is actually ready.
        # A concrete refresh/scope failure is different and can still be human-only.
        if route_id == "youtube" and OWNER_REQUEST_MARKER in text and _contains_auth_failure_keyword(text):
            return OwnerRequestDecision(
                allowed=True,
                reason="youtube_auth_failure_requires_human",
                route=route_id,
                suggested_action="YouTube token refresh/scope failure is explicitly reported.",
                checks=list(route.get("preflight") or []),
                fallback=str(route.get("fallback") or ""),
            )
        return OwnerRequestDecision(
            allowed=False,
            reason=f"route_available:{route_id}",
            route=route_id,
            suggested_action=str(route.get("command") or ""),
            checks=list(route.get("preflight") or []),
            fallback=str(route.get("fallback") or ""),
        )

    if OWNER_REQUEST_MARKER not in text:
        return OwnerRequestDecision(
            allowed=False,
            reason="missing_human_required_marker",
            route=route_id,
            suggested_action=str(route.get("command") or "Output Routesの利用可否を確認し、成果物報告へ失敗理由を書く"),
            checks=list(route.get("preflight") or []),
            fallback=str(route.get("fallback") or ""),
        )

    if not _contains_hard_human_keyword(text):
        return OwnerRequestDecision(
            allowed=False,
            reason="marker_without_hard_human_keyword",
            route=route_id,
            suggested_action=str(route.get("command") or "社員側で実行できる出口へ振り替える"),
            checks=list(route.get("preflight") or []),
            fallback=str(route.get("fallback") or ""),
        )

    return OwnerRequestDecision(
        allowed=True,
        reason="explicit_human_only",
        route=route_id,
        suggested_action="人間しかできない認証/本人確認/契約/支払い系として通す",
        checks=list(route.get("preflight") or []),
        fallback=str(route.get("fallback") or ""),
    )


def should_allow_owner_request(text: str) -> bool:
    return evaluate_owner_request(text).allowed


def should_redirect_owner_request(channel_name: str, text: str) -> bool:
    if not is_owner_request_channel_name(channel_name):
        return False
    return not should_allow_owner_request(text)


def build_redirect_notice(text: str, sender_label: str) -> str:
    decision = evaluate_owner_request(text)
    sanitized = (
        text.replace("@いくと", "いくと")
        .replace("@ikuto", "ikuto")
        .replace("@yikuto", "yikuto")
    )
    checks = "\n".join(f"- {item}" for item in decision.checks[:4]) or "- Output Routesを確認"
    action = decision.suggested_action or "社員側で公開・実装・代替成果物化する"
    fallback = decision.fallback or "失敗した場合は、失敗ルート・理由・代替公開パスを成果物報告へ残す"
    return (
        "[OWNER_REQUEST_BLOCKED]\n"
        f"{sender_label} の `いくと依頼` 投稿を抑止しました。"
        "人間待ちにせず、社員側で公開・実装・代替成果物化・失敗理由の記録まで進めてください。\n\n"
        f"判定: {decision.reason}\n"
        f"先に試す経路: {decision.route or 'route_unknown'}\n"
        f"実行: {action}\n"
        f"preflight:\n{checks}\n"
        f"fallback: {fallback}\n\n"
        "元投稿:\n"
        f"{sanitized}"
    )
