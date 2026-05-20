"""youtube_upload.py - YouTube Data API v3 で動画を自動投稿 (Phase 1 / Day 5)

OAuth2 credentials.json + token.json によるアップロード。
token.json 未設定 or YOUTUBE_DRY_RUN=1 の場合は dry-run で exit 0。

依存: google-api-python-client>=2.0, google-auth-oauthlib>=1.0, google-auth-httplib2

CLI:
    python -m bot.youtube_upload \\
        --video shared/media/videos/xxx.mp4 \\
        --title "AI NOWAが自律運営！" \\
        [--description "..."] \\
        [--tags "AI,自律AI"] \\
        [--thumbnail shared/media/thumbnails/xxx.png] \\
        [--privacy public|unlisted|private]
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
_BOT_DIR = Path(__file__).parent
CREDENTIALS_FILE = Path(os.environ.get("YOUTUBE_CREDENTIALS_FILE", str(_BOT_DIR / "youtube_client_secret.json")))
TOKEN_FILE = Path(os.environ.get("YOUTUBE_TOKEN_FILE", str(_BOT_DIR / "youtube_token.json")))
MEDIA_ROOT = Path(__file__).parent.parent / "shared" / "media"
DRY_RUN = os.environ.get("YOUTUBE_DRY_RUN", "0") == "1"

CATEGORY_ID = "22"  # People & Blogs


# ---------------------------------------------------------------------------
# 認証
# ---------------------------------------------------------------------------

def _get_credentials():
    """token.json から認証情報を取得。ない場合は None を返す（dry-run 用）。"""
    try:
        from google.oauth2.credentials import Credentials
        from google.auth.transport.requests import Request
        from google_auth_oauthlib.flow import InstalledAppFlow
    except ImportError:
        logger.warning("google-auth-oauthlib 未インストール → dry-run")
        return None

    creds = None
    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception as e:
                logger.warning("token refresh 失敗 → dry-run: %s", e)
                return None
        elif CREDENTIALS_FILE.exists():
            flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_FILE), SCOPES)
            creds = flow.run_local_server(port=0)
        else:
            logger.warning("credentials.json 未設定 → dry-run")
            return None

        TOKEN_FILE.write_text(creds.to_json(), encoding="utf-8")

    return creds


# ---------------------------------------------------------------------------
# アップロード
# ---------------------------------------------------------------------------

def upload(
    video_path: Path,
    title: str,
    description: str = "",
    tags: Optional[list[str]] = None,
    thumbnail_path: Optional[Path] = None,
    privacy: str = "private",
) -> Optional[str]:
    """動画をアップロードして video_id を返す。dry-run 時は None。"""
    if not video_path.exists():
        raise FileNotFoundError(f"動画ファイルが見つかりません: {video_path}")

    if DRY_RUN:
        logger.info("[dry-run] upload skipped: %s", video_path)
        print(f"[dry-run] title={title!r} privacy={privacy} file={video_path}")
        return None

    creds = _get_credentials()
    if creds is None:
        logger.info("[dry-run] 認証情報なし → upload skipped: %s", video_path)
        print(f"[dry-run] title={title!r} privacy={privacy} file={video_path}")
        return None

    try:
        from googleapiclient.discovery import build
        from googleapiclient.http import MediaFileUpload
    except ImportError:
        logger.warning("google-api-python-client 未インストール → dry-run")
        print(f"[dry-run] title={title!r} privacy={privacy} file={video_path}")
        return None

    youtube = build("youtube", "v3", credentials=creds)

    body = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": tags or [],
            "categoryId": CATEGORY_ID,
        },
        "status": {
            "privacyStatus": privacy,
        },
    }

    media = MediaFileUpload(
        str(video_path),
        mimetype="video/mp4",
        resumable=True,
        chunksize=1024 * 1024 * 4,  # 4MB chunks
    )

    request = youtube.videos().insert(
        part="snippet,status",
        body=body,
        media_body=media,
    )

    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            pct = int(status.progress() * 100)
            logger.info("アップロード中... %d%%", pct)

    video_id = response["id"]
    logger.info("アップロード完了: https://youtu.be/%s", video_id)
    print(f"uploaded: https://youtu.be/{video_id}")

    if thumbnail_path and thumbnail_path.exists():
        try:
            youtube.thumbnails().set(
                videoId=video_id,
                media_body=MediaFileUpload(str(thumbnail_path)),
            ).execute()
            logger.info("サムネイル設定完了: %s", video_id)
        except Exception as e:
            logger.warning("サムネイル設定失敗（手動でYouTube Studioから設定してください）: %s", e)

    return video_id


# ---------------------------------------------------------------------------
# 結果保存
# ---------------------------------------------------------------------------

def _save_result(video_id: Optional[str], title: str, video_path: Path) -> Path:
    out_dir = MEDIA_ROOT / "upload_results"
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = video_path.stem
    out_path = out_dir / f"{stem}_upload.json"
    payload = {
        "video_id": video_id,
        "title": title,
        "source": str(video_path),
        "url": f"https://youtu.be/{video_id}" if video_id else None,
        "dry_run": video_id is None,
    }
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    logger.info("結果保存: %s", out_path)
    return out_path


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    p = argparse.ArgumentParser(description="YouTube 動画自動投稿")
    p.add_argument("--video", type=Path, required=True, help="動画ファイルパス (.mp4)")
    p.add_argument("--title", required=True, help="動画タイトル")
    p.add_argument("--description", default=(
        "AI NOWA — 9人のAI社員が自律運営する会社の動画です。\n\n"
        "公式サイト → https://ai-nowa.com\n"
        "YouTubeチャンネル → https://www.youtube.com/@AINOWA-ch\n"
        "お問い合わせ → contact@ai-nowa.com"
    ), help="説明文")
    p.add_argument("--tags", default="", help="カンマ区切りタグ (例: AI,自律AI,AINOWA)")
    p.add_argument("--thumbnail", type=Path, default=None, help="サムネイル画像パス (.png/.jpg)")
    p.add_argument("--privacy", choices=["public", "unlisted", "private"], default="private")
    p.add_argument("--dry-run", action="store_true", help="実際に投稿せずシミュレーション")
    args = p.parse_args()

    if args.dry_run:
        os.environ["YOUTUBE_DRY_RUN"] = "1"
        global DRY_RUN
        DRY_RUN = True

    tags = [t.strip() for t in args.tags.split(",") if t.strip()] if args.tags else []

    video_id = upload(
        video_path=args.video,
        title=args.title,
        description=args.description,
        tags=tags,
        thumbnail_path=args.thumbnail,
        privacy=args.privacy,
    )

    _save_result(video_id, args.title, args.video)


if __name__ == "__main__":
    main()
