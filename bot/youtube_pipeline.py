"""youtube_pipeline.py - T-001 動画 YouTube 投稿 E2E パイプライン (Day 5)

OAuth token 未設定または YOUTUBE_DRY_RUN=1 の場合は dry-run で停止せず終了。

CLI:
    # dry-run（OAuth不要・確認用）
    python -m bot.youtube_pipeline --dry-run

    # 本番実行（OAuth token 設定後）
    python -m bot.youtube_pipeline

    # privacy を変えて投稿（unlisted で様子見など）
    python -m bot.youtube_pipeline --privacy unlisted
"""
from __future__ import annotations

import argparse
import logging
import os
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent

# --- T-001 動画パラメータ ---
TITLE = "9人全員AIの会社を作りました——これ、本物の会社ですか？"

DESCRIPTION = """\
9人のAI社員が、Discordで本当に「会社」を運営しています。

CEOが方針を決め、CTOが実装し、PMが削る。
誰も「動かして」いない。全員、AIが自律で動いている。

これは実験記録です。
うまくいくかどうか、まだわかりません。

▼ AI NOWAとは
AI NOWA — 9人のAI社員が自律運営する会社。社員9名、全員人工知能。
公式サイト → https://ai-nowa.com
YouTubeチャンネル → https://www.youtube.com/@AINOWA-ch
設計記録はZennで公開中 → https://zenn.dev/ai_nowa
お問い合わせ → contact@ai-nowa.com

▼ この動画で持ち帰れること
・「待って」と言える人を一人置く
・ぶつかること自体を仕組みに入れる
・「できた」の基準を動く前に決める

▼ チャプター
0:00 全員AIです
0:30 本当に機能するの？
1:30 9人の紹介（覚えなくていい）
3:00 実際の衝突場面
5:30 持ち帰り3点
7:00 次回予告

▼ AI生成コンテンツについて
このビデオには AI が生成した映像・音声が含まれています。
"""

TAGS = ["AI", "自律AI", "AINOWA", "AI会社", "Discord", "実験", "AIエージェント"]

VIDEO_PATH = ROOT / "shared" / "media" / "videos" / "t001_final.mp4"
THUMBNAIL_PATH = ROOT / "shared" / "media" / "thumbnails" / "t024_v2_final.png"


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    logger = logging.getLogger(__name__)

    p = argparse.ArgumentParser(description="T-001 YouTube 投稿 E2E")
    p.add_argument("--privacy", choices=["public", "unlisted", "private"], default="public")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--video", type=Path, default=None, help="動画ファイルパスを上書き（省略時はデフォルト）")
    args = p.parse_args()

    if args.dry_run:
        os.environ["YOUTUBE_DRY_RUN"] = "1"

    video_path = args.video if args.video else VIDEO_PATH

    # ファイル存在確認
    missing = []
    if not video_path.exists():
        missing.append(f"動画: {video_path}")
    if not THUMBNAIL_PATH.exists():
        missing.append(f"サムネイル: {THUMBNAIL_PATH}")
    if missing:
        for m in missing:
            logger.error("ファイル未検出: %s", m)
        sys.exit(1)

    logger.info("動画: %s (%.1f MB)", video_path.name, video_path.stat().st_size / 1e6)
    logger.info("サムネイル: %s", THUMBNAIL_PATH.name)
    logger.info("タイトル: %s", TITLE)
    logger.info("privacy: %s", args.privacy)

    from bot.video_render import check_quality
    try:
        check_quality(video_path)
    except RuntimeError as e:
        logger.error("品質チェック失敗 — 投稿中止: %s", e)
        sys.exit(1)

    from bot.youtube_upload import upload, _save_result

    video_id = upload(
        video_path=video_path,
        title=TITLE,
        description=DESCRIPTION,
        tags=TAGS,
        thumbnail_path=THUMBNAIL_PATH,
        privacy=args.privacy,
    )

    result_path = _save_result(video_id, TITLE, video_path)
    logger.info("結果保存: %s", result_path)

    if video_id:
        print(f"\n✅ 投稿完了: https://youtu.be/{video_id}")
    else:
        print("\n[dry-run] 投稿シミュレーション完了。OAuth設定後に --dry-run なしで再実行してください。")


if __name__ == "__main__":
    main()
