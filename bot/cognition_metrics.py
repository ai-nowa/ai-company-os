"""認知指標自動取得 (GitHub / Zenn / はてブ)。

self_improvement_loop.py からインポートして使う:
    from bot.cognition_metrics import fetch_cognition_metrics

単体テスト:
    python -m bot.cognition_metrics
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from urllib.parse import quote_plus

try:
    import requests as _requests
    _HAS_REQUESTS = True
except ImportError:
    _HAS_REQUESTS = False

GITHUB_REPO = "ai-nowa/ai-company-os"
ZENN_USERNAME = "ai_nowa"

# はてブカウント対象: サイト記事URL
HATENA_TARGET_URLS: list[str] = [
    "https://ai-nowa.com/articles/article-01/",
    "https://ai-nowa.com/articles/article-02/",
    "https://ai-nowa.com/articles/article-03/",
    "https://zenn.dev/ai_nowa/articles/procrastination-not-lazy",
    "https://zenn.dev/ai_nowa/articles/ai-nowa-failure-log",
]

JST = timezone(timedelta(hours=9))
_HEADERS = {"User-Agent": "ai-nowa-metrics/1.0"}
_TIMEOUT = 10


def _get_json(url: str) -> dict | list | None:
    if not _HAS_REQUESTS:
        return None
    try:
        r = _requests.get(url, headers=_HEADERS, timeout=_TIMEOUT)
        r.raise_for_status()
        return r.json()
    except Exception:
        return None


def _get_text(url: str) -> str | None:
    if not _HAS_REQUESTS:
        return None
    try:
        r = _requests.get(url, headers=_HEADERS, timeout=_TIMEOUT)
        r.raise_for_status()
        return r.text.strip()
    except Exception:
        return None


def _fetch_github() -> dict:
    data = _get_json(f"https://api.github.com/repos/{GITHUB_REPO}")
    if not isinstance(data, dict):
        return {"stars": 0, "forks": 0, "watchers": 0, "open_issues": 0, "error": True}
    return {
        "stars": data.get("stargazers_count", 0),
        "forks": data.get("forks_count", 0),
        "watchers": data.get("watchers_count", 0),
        "open_issues": data.get("open_issues_count", 0),
    }


def _fetch_zenn_books() -> list[dict]:
    """Zenn Book 一覧 + 各Bookのchapters_count / letters を取得。"""
    data = _get_json(f"https://zenn.dev/api/books?username={ZENN_USERNAME}")
    if not isinstance(data, dict):
        return []
    books = []
    for b in data.get("books", []):
        slug = b.get("slug", "")
        chapters_count: int | None = None
        letters: int | None = None
        detail = _get_json(f"https://zenn.dev/api/books/{slug}")
        if isinstance(detail, dict):
            chapters = detail.get("book", detail).get("chapters", detail.get("chapters", []))
            if chapters:
                chapters_count = len(chapters)
                letters = sum(c.get("body_letters_count", 0) for c in chapters)
        books.append({
            "slug": slug,
            "title": b.get("title", ""),
            "price": b.get("price", 0),
            "liked_count": b.get("liked_count", 0),
            "chapters_count": chapters_count,
            "letters": letters,
        })
    return books


def _fetch_zenn() -> dict:
    data = _get_json(
        f"https://zenn.dev/api/articles?username={ZENN_USERNAME}&count=20&order=latest"
    )
    if not isinstance(data, dict):
        return {"articles": [], "total_liked": 0, "books": [], "error": True}
    articles = []
    total_liked = 0
    for a in data.get("articles", []):
        liked = a.get("liked_count", 0)
        total_liked += liked
        articles.append({
            "slug": a.get("slug", ""),
            "title": a.get("title", ""),
            "liked_count": liked,
        })
    books = _fetch_zenn_books()
    return {"articles": articles, "total_liked": total_liked, "books": books}


def _fetch_hatena_count(url: str) -> int:
    """はてブ件数を1URLぶん取得。APIは text/plain で数値を返す。"""
    encoded = quote_plus(url)
    text = _get_text(f"https://b.hatena.ne.jp/entry/count?url={encoded}")
    if text is None:
        return 0
    try:
        return int(text)
    except ValueError:
        return 0


def _fetch_hatena(urls: list[str]) -> dict:
    counts: dict[str, int] = {}
    for url in urls:
        counts[url] = _fetch_hatena_count(url)
    return {
        "urls": counts,
        "total_bookmarks": sum(counts.values()),
    }


def fetch_cognition_metrics() -> dict:
    """全認知指標を取得して辞書で返す。各APIの失敗は 0 埋め・error フラグで継続。"""
    return {
        "github": _fetch_github(),
        "zenn": _fetch_zenn(),
        "hatena": _fetch_hatena(HATENA_TARGET_URLS),
        "collected_at": datetime.now(JST).isoformat(),
    }


if __name__ == "__main__":
    import json
    result = fetch_cognition_metrics()
    print(json.dumps(result, ensure_ascii=False, indent=2))
