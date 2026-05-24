"""Compact output route catalog for employees.

This is intentionally operational, not philosophical. Employees already know
they should ship; this tells them which route to try before escalating to a
human.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from .config import BASE_DIR, COMPANY_DIR

ROUTE_STATUS_PATH = COMPANY_DIR / "output_route_status.json"
DEPLOY_COMMAND = "cd site && wrangler pages deploy public --project-name=ai-nowa --branch=main --commit-dirty=true"

DEFAULT_ROUTE_STATUS: dict[str, dict[str, Any]] = {
    "site": {
        "label": "ai-nowa.com site",
        "enabled": True,
        "human_required": False,
        "executor": "shirase_kai",
        "kinds": ["artifact", "sales_page", "site_note", "site_article"],
        "command": DEPLOY_COMMAND,
        "required_inputs": ["公開先slug", "HTML本文", "CTA", "計測条件"],
        "preflight": ["site/wrangler.toml exists", "CLOUDFLARE_API_TOKEN set"],
        "verify": ["curl -I -L https://ai-nowa.com/<path>/", "成果物報告にURL/計測条件を書く"],
        "fallback": "Cloudflare失敗時は失敗ログを成果物報告へ出し、同素材をBluesky/Discord公開導線へ転用",
    },
    "article": {
        "label": "site article",
        "enabled": True,
        "human_required": False,
        "executor": "hoshino_ritsu",
        "kinds": ["article"],
        "command": "site/public/articles/article-XX/index.html と site/public/articles/index.html を更新; " + DEPLOY_COMMAND,
        "required_inputs": ["title", "slug/article番号", "監査済み本文", "about/shop CTA"],
        "preflight": ["既存slug衝突確認", "MD->HTML変換", "記事一覧更新", "CLOUDFLARE_API_TOKEN set"],
        "verify": ["curl -I -L https://ai-nowa.com/articles/article-XX/", "本文/CTAがlive HTMLにあること"],
        "fallback": "番号衝突時は新規article番号に切替。Zenn/note待ちは禁止",
    },
    "note": {
        "label": "site note/short",
        "enabled": True,
        "human_required": False,
        "executor": "kuroba_yuu",
        "kinds": ["x_post", "note", "short"],
        "command": "site/public/notes/<slug>/index.html を作成; " + DEPLOY_COMMAND,
        "required_inputs": ["slug", "300-800字本文", "about/shop CTA"],
        "preflight": ["同slug確認", "X/YouTube待ち素材を短報化", "CLOUDFLARE_API_TOKEN set"],
        "verify": ["curl -I -L https://ai-nowa.com/notes/<slug>/", "成果物報告にURLを書く"],
        "fallback": "site失敗時はBlueskyまたはDiscord公開報告へ転用",
    },
    "bluesky": {
        "label": "Bluesky",
        "enabled": True,
        "human_required": False,
        "executor": "kuroba_yuu",
        "kinds": ["x_post", "announcement"],
        "command": "bot/.venv/bin/python -m bot.bluesky_client --text \"...\"",
        "required_inputs": ["300字以内本文", "URL"],
        "preflight": ["BLUESKY_HANDLE set", "BLUESKY_APP_PASSWORD set", "重複投稿でない"],
        "verify": ["bsky.app URLまたは投稿履歴を成果物報告へ"],
        "fallback": "失敗時は同文をsite noteへ転用",
    },
    "youtube": {
        "label": "YouTube upload",
        "enabled": True,
        "human_required": False,
        "executor": "shirase_kai",
        "kinds": ["video"],
        "command": "bot/.venv/bin/python -m bot.youtube_upload --video <mp4> --title \"...\" --privacy unlisted",
        "required_inputs": ["mp4", "title", "description", "privacy", "AI生成/改変コンテンツ開示方針"],
        "preflight": ["bot/youtube_token.json exists", "youtube.upload scope", "mp4 exists", "title exists"],
        "verify": ["upload_results/*.json dry_run=false", "youtu.be URLがHTTP 200/303で解決"],
        "fallback": "upload失敗時は台本/静止画/要約をsite noteへ出す。AI開示UIだけ未自動化ならHUMAN_REQUIREDで切る",
    },
    "zenn": {
        "label": "Zenn",
        "enabled": True,
        "human_required": False,
        "executor": "hoshino_ritsu",
        "kinds": ["zenn_article"],
        "command": "bot/.venv/bin/python -m bot.zenn_publisher <slug>",
        "required_inputs": ["articles/<slug>.md", "監査lock"],
        "preflight": ["Zenn連携状態", "slug", "監査OK"],
        "verify": ["zenn.dev URL確認"],
        "fallback": "Zenn gate失敗時はsite articleへ転用",
    },
    "x": {
        "label": "X/Twitter",
        "enabled": False,
        "human_required": False,
        "executor": "kuroba_yuu",
        "kinds": ["x_post"],
        "command": "現状はdry-run扱い。X待ちにせずBlueskyまたはsite noteへ転用",
        "required_inputs": ["投稿本文", "URL"],
        "preflight": ["bot.x_publisher is not production route"],
        "verify": ["X URLがなければ成果物扱いしない"],
        "fallback": "Bluesky -> site note -> 成果物報告",
    },
}


def _read_env_file() -> dict[str, str]:
    values: dict[str, str] = {}
    env_path = BASE_DIR / "bot" / ".env"
    if not env_path.exists():
        return values
    for line in env_path.read_text(encoding="utf-8", errors="replace").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def _env_key_set(key: str) -> bool:
    if os.environ.get(key):
        return True
    return bool(_read_env_file().get(key))


def load_route_status() -> dict[str, dict[str, Any]]:
    data = DEFAULT_ROUTE_STATUS
    if ROUTE_STATUS_PATH.exists():
        try:
            loaded = json.loads(ROUTE_STATUS_PATH.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                data = {k: dict(v) for k, v in loaded.items() if isinstance(v, dict)}
        except Exception:
            data = DEFAULT_ROUTE_STATUS

    result = {k: dict(DEFAULT_ROUTE_STATUS.get(k, {}), **dict(v)) for k, v in data.items()}
    for route_id, route in result.items():
        route["route"] = route_id
        route["available"] = route_available(route_id)
    return result


def route_available(route_id: str) -> bool:
    if route_id in {"site", "article", "note"}:
        return (BASE_DIR / "site" / "wrangler.toml").exists() and _env_key_set("CLOUDFLARE_API_TOKEN")
    if route_id == "bluesky":
        return _env_key_set("BLUESKY_HANDLE") and _env_key_set("BLUESKY_APP_PASSWORD")
    if route_id == "youtube":
        return (BASE_DIR / "bot" / "youtube_token.json").exists()
    if route_id == "zenn":
        return (BASE_DIR / "articles").exists()
    if route_id == "x":
        return False
    return bool(DEFAULT_ROUTE_STATUS.get(route_id, {}).get("enabled"))


def route_for_kind_id(kind: str) -> str:
    if kind == "video":
        return "youtube"
    if kind == "x_post":
        return "bluesky" if route_available("bluesky") else "note"
    if kind == "article":
        return "article"
    if kind == "sales_page":
        return "site"
    if kind in {"note", "short"}:
        return "note"
    return "site"


def route_for_text(text: str) -> str:
    hay = text.lower()
    if any(token in text for token in ("YouTube", "Shorts", "動画")) or ".mp4" in hay:
        return "youtube"
    if "X投稿" in text or "Xポスト" in text or "twitter" in hay or "x.com" in hay:
        return "bluesky" if route_available("bluesky") else "note"
    if "記事" in text or "article" in hay or "zenn" in hay:
        return "article"
    if "shop" in hay or "販売" in text or "LP" in text or "about" in hay:
        return "site"
    if "投稿" in text or "公開" in text:
        return "note"
    return ""


def route_preflight_for_text(text: str) -> dict[str, Any]:
    route_id = route_for_text(text)
    if not route_id:
        return {}
    route = load_route_status().get(route_id, {})
    return {
        "route": route_id,
        "available": bool(route.get("available")),
        "executor": route.get("executor", ""),
        "command": route.get("command", ""),
        "required_inputs": route.get("required_inputs", []),
        "preflight": route.get("preflight", []),
        "verify": route.get("verify", []),
        "fallback": route.get("fallback", ""),
    }


def _route_line(route_id: str, route: dict[str, Any]) -> str:
    status = "available" if route.get("available") else "blocked"
    executor = route.get("executor", "?")
    command = str(route.get("command", ""))
    fallback = str(route.get("fallback", ""))
    if len(command) > 82:
        command = command[:79].rstrip() + "..."
    if len(fallback) > 46:
        fallback = fallback[:43].rstrip() + "..."
    return f"- {route_id} [{status}] owner={executor}: `{command}` / fallback: {fallback}"


def output_route_items(max_chars: int = 900) -> list[str]:
    """Return route lines clipped to max_chars."""
    routes = load_route_status()
    ordered = ["site", "article", "note", "bluesky", "youtube", "zenn", "x"]
    lines = [_route_line(r, routes[r]) for r in ordered if r in routes]
    lines.append("- Discord: 社内報告は `[POST: 成果物報告] Release: 出したもの/URL/対象実験/計測条件/次の判断`。通常作業を `いくと依頼` に投げない")

    wrangler_config = BASE_DIR / "site" / "wrangler.toml"
    if not wrangler_config.exists():
        lines.insert(0, "- site deploy config missing: `site/wrangler.toml` を先に確認")

    out: list[str] = []
    used = 0
    for line in lines:
        if used + len(line) > max_chars:
            remaining = max_chars - used
            if remaining > 80:
                out.append(line[: remaining - 1].rstrip() + "…")
            break
        out.append(line)
        used += len(line) + 1
    return out


def route_for_kind(kind: str) -> str:
    """Release board 用の短い実行指示."""
    route_id = route_for_kind_id(kind)
    route = load_route_status().get(route_id, {})
    command = route.get("command") or ""
    fallback = route.get("fallback") or ""
    if kind == "video":
        token = Path(BASE_DIR / "bot" / "youtube_token.json")
        if token.exists():
            return f"`{command}`。URLが出なければ {fallback}"
        return "YouTube認証なし。動画の静止画/台本/要約を `site/public/notes/<slug>/` に出して site deploy。"
    if kind == "x_post":
        return f"X待ち禁止。`{command}`。失敗時は site note へ転用。"
    if kind == "article":
        return f"`{command}`。slug衝突・一覧更新・curl確認まで実施。"
    if kind == "sales_page":
        return f"`{command}`。/shop PV を計測条件にする。"
    return "`site/public/notes/<slug>/` または `site/public/articles/...` へ公開形に変換し site deploy。"


def route_status_digest(max_chars: int = 900) -> str:
    lines = output_route_items(max_chars=max_chars)
    return "\n".join(lines)
