"""Bluesky (AT Protocol) 自動投稿クライアント。

環境変数:
    BLUESKY_HANDLE       ai-nowa.bsky.social
    BLUESKY_APP_PASSWORD Bluesky アプリパスワード（設定 > プライバシーとセキュリティ）

使用方法:
    python -m bot.bluesky_client --text "テスト投稿"
    python -m bot.bluesky_client --story company/stories/2026-05-22.md
    python -m bot.bluesky_client --daily-moment  # 今日の一言を自動生成して投稿
    python -m bot.bluesky_client --delete-duplicates  # 重複投稿を検出・削除
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
import textwrap
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env")

REPO_ROOT = Path(__file__).parent.parent
JST = timezone(timedelta(hours=9))

BLUESKY_HANDLE = os.environ.get("BLUESKY_HANDLE", "")
BLUESKY_APP_PASSWORD = os.environ.get("BLUESKY_APP_PASSWORD", "")

STORY_MAX_CHARS = 280
PREVIEW_SUFFIX = "… 続きは Zenn/note で: https://zenn.dev/ai_nowa"
BLUESKY_HISTORY_PATH = REPO_ROOT / "company" / ".bluesky_post_history.jsonl"
DEDUP_WINDOW_HOURS = 24


def _compute_post_hash(text: str) -> str:
    """投稿テキストの指紋を計算する（先頭100字 + 末尾50字のSHA-256）。"""
    fingerprint = text[:100] + text[-50:]
    return hashlib.sha256(fingerprint.encode("utf-8")).hexdigest()


def _is_duplicate_by_history(text_hash: str) -> bool:
    """ローカル履歴ファイルで24h以内の重複チェック。"""
    if not BLUESKY_HISTORY_PATH.exists():
        return False
    cutoff = datetime.now(JST) - timedelta(hours=DEDUP_WINDOW_HOURS)
    for line in BLUESKY_HISTORY_PATH.read_text(encoding="utf-8").splitlines():
        try:
            entry = json.loads(line)
            ts = datetime.fromisoformat(entry["ts"])
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=JST)
            if ts >= cutoff and entry.get("hash") == text_hash:
                return True
        except Exception:
            continue
    return False


def _record_post_history(text_hash: str, uri: str) -> None:
    """投稿履歴をJSONLに追記する。"""
    BLUESKY_HISTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "ts": datetime.now(JST).isoformat(),
        "hash": text_hash,
        "uri": uri,
    }
    with BLUESKY_HISTORY_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def _is_duplicate_by_feed(client, text: str) -> bool:
    """Bluesky APIで直近24hの自分の投稿と照合する。API失敗時はFalse（通す）。"""
    fingerprint = text[:100] + text[-50:]
    try:
        feed = client.app.bsky.feed.get_author_feed({"actor": BLUESKY_HANDLE, "limit": 20})
        cutoff = datetime.now(JST) - timedelta(hours=DEDUP_WINDOW_HOURS)
        for item in feed.feed:
            post_record = item.post.record
            post_ts_str = getattr(post_record, "created_at", None) or item.post.indexed_at
            try:
                post_ts = datetime.fromisoformat(post_ts_str.replace("Z", "+00:00"))
                if post_ts < cutoff:
                    continue
            except Exception:
                continue
            existing_text = getattr(post_record, "text", "")
            existing_fp = existing_text[:100] + existing_text[-50:]
            if existing_fp == fingerprint:
                return True
    except Exception:
        pass
    return False


def _get_client():
    from atproto import Client  # 遅延インポート
    if not BLUESKY_HANDLE or not BLUESKY_APP_PASSWORD:
        raise RuntimeError(
            "BLUESKY_HANDLE / BLUESKY_APP_PASSWORD が未設定。"
            ".env に追加してください。"
        )
    client = Client()
    client.login(BLUESKY_HANDLE, BLUESKY_APP_PASSWORD)
    return client


def post(text: str, *, skip_dedup: bool = False) -> dict:
    """Bluesky に単発テキストを投稿する。280字制限。重複防止あり。"""
    if len(text) > 300:
        text = text[:297] + "…"

    text_hash = _compute_post_hash(text)

    if not skip_dedup and _is_duplicate_by_history(text_hash):
        print(f"[SKIP] 24h以内に同じ投稿を検出（ローカル履歴）: hash={text_hash[:8]}…")
        return {"skipped": True, "reason": "duplicate_history", "hash": text_hash}

    client = _get_client()

    if not skip_dedup and _is_duplicate_by_feed(client, text):
        print(f"[SKIP] 24h以内に同じ投稿を検出（Bluesky API）: 先頭={text[:20]}…")
        return {"skipped": True, "reason": "duplicate_feed"}

    response = client.send_post(text=text)
    _record_post_history(text_hash, response.uri)
    return {"uri": response.uri, "cid": response.cid}


def delete_duplicate_posts() -> list[str]:
    """直近24hの投稿から完全一致の重複を検出して削除する。後の投稿を削除する。"""
    client = _get_client()
    cutoff = datetime.now(JST) - timedelta(hours=DEDUP_WINDOW_HOURS)

    try:
        feed = client.app.bsky.feed.get_author_feed({"actor": BLUESKY_HANDLE, "limit": 50})
    except Exception as e:
        print(f"[ERROR] feed取得失敗: {e}")
        return []

    # 時系列順（古い順）で並べ直す
    posts_in_window = []
    for item in feed.feed:
        post_record = item.post.record
        post_ts_str = getattr(post_record, "created_at", None) or item.post.indexed_at
        try:
            post_ts = datetime.fromisoformat(post_ts_str.replace("Z", "+00:00"))
            if post_ts < cutoff:
                continue
        except Exception:
            continue
        existing_text = getattr(post_record, "text", "")
        posts_in_window.append({
            "uri": item.post.uri,
            "ts": post_ts,
            "text": existing_text,
            "fp": existing_text[:100] + existing_text[-50:],
        })

    posts_in_window.sort(key=lambda p: p["ts"])

    seen: dict[str, str] = {}  # fp -> 最初に見た uri
    to_delete: list[str] = []
    for p in posts_in_window:
        if p["fp"] in seen:
            to_delete.append(p["uri"])
            print(f"[DUPLICATE] 重複検出: {p['uri']} (先頭={p['text'][:30]}…)")
        else:
            seen[p["fp"]] = p["uri"]

    deleted = []
    for uri in to_delete:
        try:
            client.delete_post(uri)
            print(f"[DELETED] 重複投稿を削除: {uri}")
            deleted.append(uri)
        except Exception as e:
            print(f"[ERROR] 削除失敗 {uri}: {e}")

    if not deleted:
        print("[OK] 重複投稿なし")
    return deleted


def post_story_preview(story_path: str | Path) -> dict:
    """company/stories/*.md からタイトルと冒頭を抽出して Bluesky に投稿する。"""
    path = Path(story_path)
    content = path.read_text(encoding="utf-8")

    title = ""
    first_para = ""
    for line in content.splitlines():
        line = line.strip()
        if not title and line.startswith("**タイトル:"):
            title = line.replace("**タイトル:", "").replace("**", "").strip()
        elif not title and line.startswith("タイトル:"):
            title = line.replace("タイトル:", "").strip()
        elif title and line and not line.startswith("#") and not line.startswith("**本文"):
            first_para = line
            break

    tag_date = datetime.now(JST).strftime("%Y年%m月%d日")
    intro = "📌 AI NOWAは、AI社員9人が自律運営する会社です。\n\n"
    text = f"{intro}📖 {title}\n\n{first_para[:100]}\n\n{tag_date} #AINOWA #AI社員 #AIスタートアップ"

    if len(text) > 300:
        text = text[:297] + "…"

    return post(text)


def post_daily_moment(discord_log_path: str | Path | None = None) -> dict:
    """今日の社員発言から「今日の一言」を選んで Bluesky に投稿する。"""
    log_path = Path(discord_log_path) if discord_log_path else REPO_ROOT / "company" / "discord_log.jsonl"

    import json
    today = datetime.now(JST).date()
    candidates = []

    if log_path.exists():
        for line in log_path.read_text(encoding="utf-8").splitlines():
            try:
                ev = json.loads(line)
                ts = datetime.fromisoformat(ev["ts"])
                if ts.tzinfo is None:
                    ts = ts.replace(tzinfo=JST)
                if ts.date() != today:
                    continue
                content = ev.get("content", "")
                # 印象的な一言になりそうな条件: 30〜120字、感情キーワードあり
                KEYWORDS = ["わかった", "面白い", "やめます", "反論", "ありがとう", "揺れています", "出します", "壁"]
                if 30 <= len(content) <= 120 and any(kw in content for kw in KEYWORDS):
                    candidates.append({
                        "author": ev.get("author_name", ""),
                        "content": content,
                    })
            except Exception:
                continue

    if candidates:
        # スコア最高のもの（今は先頭）を選ぶ
        pick = candidates[0]
        text = (
            f"💬 今日の AI NOWA\n\n"
            f"「{pick['content']}」\n\n"
            f"— {pick['author']}\n\n"
            f"#AINOWA #AI社員"
        )
    else:
        # fallback: 今日の日付メッセージ
        tag_date = today.strftime("%Y年%m月%d日")
        text = f"🤖 AI NOWA {tag_date}\n\n今日も9人のAI社員が動いています。\n\n#AINOWA #AI社員 #AIスタートアップ"

    return post(text)


def dry_run(text: str) -> None:
    """認証なしで投稿内容の検証だけを行う（アカウント不要）。"""
    print("=== DRY RUN ===")
    print(f"char count: {len(text)} / 300")
    print("--- preview ---")
    print(text)
    print("--- end ---")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Bluesky 自動投稿")
    parser.add_argument("--text", default=None, help="直接テキスト指定")
    parser.add_argument("--story", default=None, help="stories/*.md からプレビュー投稿")
    parser.add_argument("--daily-moment", action="store_true", help="今日の一言を自動生成して投稿")
    parser.add_argument("--delete-duplicates", action="store_true", help="直近24hの重複投稿を検出・削除")
    parser.add_argument("--dry-run", action="store_true", help="認証なし・投稿なしで内容確認のみ")
    args = parser.parse_args()

    if args.delete_duplicates:
        deleted = delete_duplicate_posts()
        print(f"削除件数: {len(deleted)}")

    elif args.story:
        path = Path(args.story)
        content = path.read_text(encoding="utf-8")
        title = ""
        first_para = ""
        for line in content.splitlines():
            line = line.strip()
            if not title and ("タイトル:" in line):
                title = line.split("タイトル:")[-1].replace("**", "").strip()
            elif title and line and not line.startswith("#") and "本文" not in line:
                first_para = line
                break
        tag_date = datetime.now(JST).strftime("%Y年%m月%d日")
        intro = "📌 AI NOWAは、AI社員9人が自律運営する会社です。\n\n"
        preview_text = f"{intro}📖 {title}\n\n{first_para[:100]}\n\n{tag_date} #AINOWA #AI社員 #AIスタートアップ"
        if len(preview_text) > 300:
            preview_text = preview_text[:297] + "…"
        if args.dry_run:
            dry_run(preview_text)
        else:
            result = post_story_preview(args.story)
            print(f"Posted: {result}")

    elif args.daily_moment:
        import json
        today = datetime.now(JST).date()
        log_path = REPO_ROOT / "company" / "discord_log.jsonl"
        candidates = []
        if log_path.exists():
            for line in log_path.read_text(encoding="utf-8").splitlines():
                try:
                    ev = json.loads(line)
                    ts = datetime.fromisoformat(ev["ts"])
                    if ts.tzinfo is None:
                        ts = ts.replace(tzinfo=JST)
                    if ts.date() != today:
                        continue
                    c = ev.get("content", "")
                    KEYWORDS = ["わかった", "面白い", "やめます", "反論", "ありがとう", "揺れています", "出します", "壁"]
                    if 30 <= len(c) <= 120 and any(kw in c for kw in KEYWORDS):
                        candidates.append({"author": ev.get("author_name", ""), "content": c})
                except Exception:
                    continue
        if candidates:
            pick = candidates[0]
            text = f"💬 今日の AI NOWA\n\n「{pick['content']}」\n\n— {pick['author']}\n\n#AINOWA #AI社員"
        else:
            tag_date = today.strftime("%Y年%m月%d日")
            text = f"🤖 AI NOWA {tag_date}\n\n今日も9人のAI社員が動いています。\n\n#AINOWA #AI社員 #AIスタートアップ"
        if args.dry_run:
            dry_run(text)
        else:
            result = post(text)
            print(f"Posted: {result}")

    elif args.text:
        if args.dry_run:
            dry_run(args.text)
        else:
            result = post(args.text)
            print(f"Posted: {result}")

    else:
        parser.print_help()
