"""Owner request gate.

AI NOWA は「人間を動かさないための会社」なので、社員が安易に
`いくと依頼` へ公開・投稿・確認作業を投げるのを止める。
本当に人間しかできない認証/本人確認/契約系だけ、明示マーカー付きで通す。
"""
from __future__ import annotations

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


def is_owner_request_channel_name(channel_name: str) -> bool:
    return any(marker in channel_name for marker in OWNER_CHANNEL_MARKERS)


def should_allow_owner_request(text: str) -> bool:
    if OWNER_REQUEST_MARKER not in text:
        return False
    lowered = text.lower()
    return any(keyword.lower() in lowered for keyword in HARD_HUMAN_KEYWORDS)


def should_redirect_owner_request(channel_name: str, text: str) -> bool:
    if not is_owner_request_channel_name(channel_name):
        return False
    return not should_allow_owner_request(text)


def build_redirect_notice(text: str, sender_label: str) -> str:
    sanitized = (
        text.replace("@いくと", "いくと")
        .replace("@ikuto", "ikuto")
        .replace("@yikuto", "yikuto")
    )
    return (
        "[OWNER_REQUEST_BLOCKED]\n"
        f"{sender_label} の `いくと依頼` 投稿を抑止しました。"
        "人間待ちにせず、社員側で公開・実装・代替成果物化・失敗理由の記録まで進めてください。\n\n"
        "元投稿:\n"
        f"{sanitized}"
    )
