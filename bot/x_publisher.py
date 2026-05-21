"""X (Twitter) 投稿自動化モジュール。

dry_run=True の間は実投稿せず、preview/logs/x_dry_run/ にファイル出力する。
APIキー取得後に dry_run=False で実投稿に切り替える。
"""
from __future__ import annotations

import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional

BOT_DIR = Path(__file__).parent
CREDENTIALS_FILE = BOT_DIR / "x_credentials.json"
DRY_RUN_DIR = BOT_DIR.parent / "shared" / "x_dry_run_preview"

JST = timezone(timedelta(hours=9))


def _load_credentials() -> dict:
    if not CREDENTIALS_FILE.exists():
        raise FileNotFoundError(
            f"X credentials not found: {CREDENTIALS_FILE}\n"
            "Run x_credentials_import.py after ikuto sets up the Developer Account."
        )
    return json.loads(CREDENTIALS_FILE.read_text(encoding="utf-8"))


def _get_tweepy_client():
    """tweepy.Client を返す。APIキー未設定時は ImportError or FileNotFoundError。"""
    try:
        import tweepy
    except ImportError as e:
        raise ImportError("tweepy not installed. Run: pip install tweepy") from e

    creds = _load_credentials()
    return tweepy.Client(
        consumer_key=creds["api_key"],
        consumer_secret=creds["api_secret"],
        access_token=creds["access_token"],
        access_token_secret=creds["access_token_secret"],
    )


def post_tweet(
    text: str,
    image_path: Optional[str | Path] = None,
    dry_run: bool = True,
) -> dict:
    """テキスト（＋オプション静止画）を X に投稿する。

    Args:
        text: 投稿本文（280文字以内）
        image_path: 静止画ファイルパス。None なら テキストのみ
        dry_run: True の間は実投稿せずファイルに保存（デフォルト True）

    Returns:
        {"status": "dry_run"|"posted", "preview_path": ..., "tweet_id": ...}
    """
    if len(text) > 280:
        raise ValueError(f"Tweet text too long: {len(text)} chars (max 280)")

    ts = datetime.now(JST).strftime("%Y%m%d_%H%M%S")

    if dry_run:
        DRY_RUN_DIR.mkdir(parents=True, exist_ok=True)
        preview = {
            "ts": datetime.now(JST).isoformat(),
            "text": text,
            "image_path": str(image_path) if image_path else None,
            "char_count": len(text),
        }
        out = DRY_RUN_DIR / f"{ts}_preview.json"
        out.write_text(json.dumps(preview, ensure_ascii=False, indent=2), encoding="utf-8")
        return {"status": "dry_run", "preview_path": str(out)}

    # --- 実投稿（APIキー取得後に有効化）---
    client = _get_tweepy_client()

    media_id = None
    if image_path:
        media_id = _upload_image(image_path)

    kwargs: dict = {"text": text}
    if media_id:
        kwargs["media_ids"] = [media_id]

    response = client.create_tweet(**kwargs)
    tweet_id = response.data["id"]
    return {"status": "posted", "tweet_id": tweet_id}


def _upload_image(image_path: str | Path) -> str:
    """静止画を X にアップロードして media_id を返す（v1.1 API）。"""
    try:
        import tweepy
    except ImportError as e:
        raise ImportError("tweepy not installed") from e

    creds = _load_credentials()
    auth = tweepy.OAuth1UserHandler(
        creds["api_key"],
        creds["api_secret"],
        creds["access_token"],
        creds["access_token_secret"],
    )
    api_v1 = tweepy.API(auth)
    media = api_v1.media_upload(str(image_path))
    return media.media_id_string


def build_episode_tweet(
    title: str,
    summary: str,
    episode_num: int,
    zenn_url: Optional[str] = None,
) -> str:
    """AI Historian型エピソードの投稿本文を生成する。

    Returns:
        投稿本文文字列（280文字以内に収まるよう調整）
    """
    url_part = f"\n\n{zenn_url}" if zenn_url else ""
    body = f"【AI検証 #{episode_num:02d}】{title}\n\n{summary}{url_part}"

    if len(body) > 280:
        # summaryを短縮
        max_summary = 280 - len(f"【AI検証 #{episode_num:02d}】{title}\n\n...{url_part}")
        body = f"【AI検証 #{episode_num:02d}】{title}\n\n{summary[:max_summary]}...{url_part}"

    return body
