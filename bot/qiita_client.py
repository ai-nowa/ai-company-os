"""Qiita 自動投稿クライアント。

環境変数:
    QIITA_ACCESS_TOKEN  Qiita の個人用アクセストークン（設定 > アプリケーション）

使用方法:
    python -m bot.qiita_client --story-md company/stories/2026-05-22.md
    python -m bot.qiita_client --dry-run --story-md company/stories/2026-05-22.md
    python -m bot.qiita_client --list  # 投稿済み記事一覧
"""
from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env")

REPO_ROOT = Path(__file__).parent.parent
JST = timezone(timedelta(hours=9))

QIITA_API_BASE = "https://qiita.com/api/v2"
QIITA_ACCESS_TOKEN = os.environ.get("QIITA_ACCESS_TOKEN", "")
QIITA_HISTORY_PATH = REPO_ROOT / "company" / ".qiita_post_history.jsonl"

DEFAULT_TAGS = [
    {"name": "AI", "versions": []},
    {"name": "生成AI", "versions": []},
    {"name": "AIエージェント", "versions": []},
    {"name": "Claude", "versions": []},
]


def _is_duplicate_title(title: str) -> bool:
    """ローカル履歴でタイトルの重複チェック。"""
    if not QIITA_HISTORY_PATH.exists():
        return False
    title_hash = hashlib.sha256(title.encode("utf-8")).hexdigest()
    for line in QIITA_HISTORY_PATH.read_text(encoding="utf-8").splitlines():
        try:
            entry = json.loads(line)
            if entry.get("title_hash") == title_hash:
                return True
        except Exception:
            continue
    return False


def _record_qiita_history(title: str, article_id: str) -> None:
    """投稿履歴をJSONLに追記する。"""
    QIITA_HISTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
    title_hash = hashlib.sha256(title.encode("utf-8")).hexdigest()
    entry = {
        "ts": datetime.now(JST).isoformat(),
        "title_hash": title_hash,
        "title": title,
        "id": article_id,
    }
    with QIITA_HISTORY_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def _headers() -> dict:
    if not QIITA_ACCESS_TOKEN:
        raise RuntimeError(
            "QIITA_ACCESS_TOKEN が未設定。.env に追加してください。"
        )
    return {
        "Authorization": f"Bearer {QIITA_ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }


def post_article(
    title: str,
    body: str,
    tags: list[dict] | None = None,
    is_private: bool = True,
    skip_dedup: bool = False,
) -> dict:
    """Qiita に記事を投稿する。デフォルトは非公開（確認後に公開する運用）。"""
    if not skip_dedup and _is_duplicate_title(title):
        print(f"[SKIP] 同タイトルの投稿履歴を検出: {title}")
        return {"skipped": True, "reason": "duplicate_title", "title": title}

    payload = {
        "title": title,
        "body": body,
        "tags": tags or DEFAULT_TAGS,
        "private": is_private,
        "tweet": False,
    }
    resp = requests.post(
        f"{QIITA_API_BASE}/items",
        headers=_headers(),
        json=payload,
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    _record_qiita_history(title, data["id"])
    return {"id": data["id"], "url": data["url"], "title": data["title"]}


def post_from_story(story_path: str | Path, is_private: bool = True) -> dict:
    """company/stories/*.md を Qiita 記事として投稿する。"""
    path = Path(story_path)
    content = path.read_text(encoding="utf-8")

    # タイトル抽出
    title = f"AI NOWA日誌 {datetime.now(JST).strftime('%Y-%m-%d')}"
    for line in content.splitlines():
        line = line.strip()
        if "タイトル:" in line:
            title = line.split("タイトル:")[-1].replace("**", "").strip()
            break

    # 本文をQiita向けに整形（編集メモ節は除外）
    body_lines = []
    in_editorial = False
    for line in content.splitlines():
        if "編集メモ" in line:
            in_editorial = True
            continue
        if in_editorial:
            continue
        body_lines.append(line)

    body = "\n".join(body_lines).strip()
    body += "\n\n---\n\n> この記事は AI 社員「白瀬カイ（CTO）」が自動生成した下書きです。\n> 編集長「星野リツ」が推敲後に公開します。\n"

    return post_article(title=title, body=body, is_private=is_private)


def list_articles(per_page: int = 10) -> list[dict]:
    """自分の投稿記事一覧を取得する。"""
    resp = requests.get(
        f"{QIITA_API_BASE}/authenticated_user/items",
        headers=_headers(),
        params={"per_page": per_page},
        timeout=30,
    )
    resp.raise_for_status()
    return [{"id": a["id"], "title": a["title"], "url": a["url"]} for a in resp.json()]


def dry_run(story_path: str | Path) -> None:
    """認証なしで投稿内容の検証のみ行う。"""
    path = Path(story_path)
    content = path.read_text(encoding="utf-8")
    title = f"AI NOWA日誌 {datetime.now(JST).strftime('%Y-%m-%d')}"
    for line in content.splitlines():
        if "タイトル:" in line:
            title = line.split("タイトル:")[-1].replace("**", "").strip()
            break

    print("=== QIITA DRY RUN ===")
    print(f"title: {title}")
    print(f"tags: {[t['name'] for t in DEFAULT_TAGS]}")
    print(f"char count: {len(content)}")
    print(f"private: True（確認後に公開）")
    print("--- body preview (first 200 chars) ---")
    print(content[:200])
    print("--- end ---")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Qiita 自動投稿")
    parser.add_argument("--story-md", default=None, help="stories/*.md ファイルパス")
    parser.add_argument("--public", action="store_true", help="公開投稿（デフォルトは非公開）")
    parser.add_argument("--list", action="store_true", help="投稿済み記事一覧を表示")
    parser.add_argument("--dry-run", action="store_true", help="投稿なしで内容確認のみ")
    args = parser.parse_args()

    if args.list:
        articles = list_articles()
        for a in articles:
            print(f"{a['id']}: {a['title']} ({a['url']})")

    elif args.story_md:
        if args.dry_run:
            dry_run(args.story_md)
        else:
            result = post_from_story(args.story_md, is_private=not args.public)
            print(f"Posted: {result}")

    else:
        # 今日のストーリーが存在すれば自動で対象にする
        today_story = REPO_ROOT / "company" / "stories" / f"{datetime.now(JST).date()}.md"
        if today_story.exists():
            if args.dry_run:
                dry_run(today_story)
            else:
                result = post_from_story(today_story, is_private=not args.public)
                print(f"Posted: {result}")
        else:
            parser.print_help()
