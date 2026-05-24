"""Compact output route catalog for employees.

This is intentionally operational, not philosophical. Employees already know
they should ship; this tells them which route to try before escalating to a
human.
"""
from __future__ import annotations

from pathlib import Path

from .config import BASE_DIR

ROUTE_LINES = [
    "- site: `site/public/...` を編集 -> `cd site && wrangler pages deploy public --project-name=ai-nowa --branch=main --commit-dirty=true` -> `https://ai-nowa.com/...` を成果物報告",
    "- article: 監査OK本文は `site/public/articles/article-XX/index.html` と `site/public/articles/index.html` に反映して site deploy",
    "- note/short: SNS本文・短報は `site/public/notes/<slug>/index.html` にして site deploy。X/YouTube待ちの代替に使う",
    "- about/shop: `/about` `/shop` は `site/public/about|shop/index.html` を更新し site deploy。導線検証は /shop PV を最小成功にする",
    "- Bluesky: `bot/.venv/bin/python -m bot.bluesky_client --text \"...\"`。認証失敗なら同文を site note へ転用",
    "- YouTube: `bot/.venv/bin/python -m bot.youtube_upload --video <mp4> --title \"...\" --privacy unlisted`。dry-run/no URLなら静止画・台本・短報を site note へ転用",
    "- Zenn: `articles/<slug>.md` と監査lockがある時だけ `bot/.venv/bin/python -m bot.zenn_publisher <slug>`。Gate失敗なら site article",
    "- X: 現状は `bot.x_publisher` dry-run中心。人間投稿待ちにせず、Bluesky または site note へ転用",
    "- Discord: 社内報告は `[POST: 成果物報告] Release: 出したもの/URL/対象実験/計測条件/次の判断`。通常作業を `いくと依頼` に投げない",
]


def output_route_items(max_chars: int = 900) -> list[str]:
    """Return route lines clipped to max_chars."""
    # Cloudflare deploy が使えない環境でも「何を試すべきか」は同じなので、
    # ここでは存在確認だけを補助情報として足す。
    lines = list(ROUTE_LINES)
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
    if kind == "video":
        token = Path(BASE_DIR / "bot" / "youtube_token.json")
        if token.exists():
            return "`python -m bot.youtube_upload --video <mp4> --title ... --privacy unlisted`。URLが出なければ site note へ転用。"
        return "YouTube認証なし。動画の静止画/台本/要約を `site/public/notes/<slug>/` に出して site deploy。"
    if kind == "x_post":
        return "X待ち禁止。同文を `python -m bot.bluesky_client --text ...`、失敗時は `site/public/notes/<slug>/` へ転用。"
    if kind == "article":
        return "`site/public/articles/article-XX/index.html` と一覧を更新し、`cd site && wrangler pages deploy public --project-name=ai-nowa --branch=main --commit-dirty=true`。"
    if kind == "sales_page":
        return "`site/public/shop/index.html` または `/about` 導線を更新し site deploy。/shop PV を計測条件にする。"
    return "`site/public/notes/<slug>/` または `site/public/articles/...` へ公開形に変換し site deploy。"
