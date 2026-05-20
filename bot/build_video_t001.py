"""build_video_t001.py - T-001 動画コンテンツ生成（台本v3.3）

テキストカード画像 + gTTS音声 → video_render.py → t001_final.mp4

CLI:
    python -m bot.build_video_t001 [--dry-run]
"""
from __future__ import annotations

import argparse
import logging
import json
from pathlib import Path
from typing import Optional

from PIL import Image, ImageDraw, ImageFont

logger = logging.getLogger(__name__)

ROOT = Path(__file__).parent.parent
MEDIA_ROOT = ROOT / "shared" / "media"
CARDS_DIR = MEDIA_ROOT / "t001_cards"
AUDIO_DIR = MEDIA_ROOT / "t001_audio"
VIDEO_OUT = MEDIA_ROOT / "videos" / "t001_final.mp4"

FONT_PATH = "/home/ikuto/.local/share/fonts/NotoSansJP.ttf"
W, H = 1280, 720
BG = (15, 15, 20)
TEXT_COLOR = (230, 230, 235)
ACCENT = (88, 101, 242)  # CTO blue

# 台本v3.3 各カードの定義 (画面テキスト, ナレーション)
CARDS = [
    # ① フック
    (
        "全員\nAI\nです。",
        "Discordというチャットツールで動く、ある会社の会議の様子です。",
        "hook_01",
    ),
    (
        "社長も、部長も、\n監査役も。\n人間は画面の外。",
        "これ、全員AIです。社長も、部長も、監査役も。人間は画面の外で見ているだけ。",
        "hook_02",
    ),
    (
        "今日も朝9時から\n会議が始まりました。",
        "今日も朝9時から会議が始まりました。",
        "hook_03",
    ),
    # ② 問い
    (
        "「会社を動かす」は\n仕事を頼むのとは\n全然違いました。",
        "AIに仕事をさせたことがある人は多いと思います。でも「会社を動かす」は、仕事を頼むのとは全然違いました。",
        "question_01",
    ),
    (
        "9人で議論しながら\n意思決定するのは\n別の話でした。",
        "AIに文章を1本書かせるのと、9人で議論しながら意思決定するのは、別の話でした。",
        "question_02",
    ),
    (
        "どうやって止めるか、\nが最初の問題でした。",
        "どうやって動かすか、じゃなくて、どうやって止めるか、が最初の問題でした。",
        "question_03",
    ),
    # ③ AI NOWA紹介
    (
        "AI NOWA\n9人のAI社員",
        "この会社の名前はAI NOWA。9人のAI社員がいます。AIだけで、本当に会社が動くのか。その実験です。",
        "intro_01",
    ),
    (
        "有馬レイジ CEO\n「やれ」で全部始まる\n\n三枝ミオ COO\n「実行可能か確認します」\n\n白瀬カイ CTO\n「技術的には正しい」",
        "全員覚えなくていい。今日は「こういう役割の人たちがいる」、それだけで十分です。",
        "intro_02",
    ),
    (
        "朝倉ノア PM\n「それ、削れます」\n\n星野リツ 編集長\n「起承転結ある？」\n\n黒羽ユウ マーケ\n「この数字、どこに効く？」",
        "9人に役割があって、お互いを呼び合って、止め合って、それで会社が動いています。",
        "intro_03",
    ),
    (
        "神楽アオイ 監査\n「一旦止めます」\n\n森永ハル People\n「誰か話を聞いてる？」\n\n日向ナギ 視聴者代表\n「初見には伝わらない」",
        "監査役が止める。Peopleが気遣う。視聴者代表が「わからない」と言う。それぞれが機能しています。",
        "intro_04",
    ),
    # ④ 実際の場面
    (
        "先週、初めて本当に\n社員同士が衝突しました。",
        "でも、うまくいかない時があります。先週、初めて本当に社員同士が衝突しました。",
        "scene_01",
    ),
    (
        "CTO:\n「技術が完成した」\n\nPM:\n「読者に届いていない」",
        "CTOは「技術が完成した」と言った。PMは「読者に届いていない」と言った。どっちも間違っていない。それが問題でした。",
        "scene_02",
    ),
    (
        "監査役アオイ:\n「整えてから出す」",
        "そこで止めに入ったのが、監査役のアオイでした。アオイの仕事は「公開を止める」ことじゃない。「整えてから出す」ことです。",
        "scene_03",
    ),
    # ⑤ 持ち帰り
    (
        "気づいた3つのこと",
        "この会社を見ていて、気づいたことが3つあります。",
        "tips_00",
    ),
    (
        "① 止める役がいないと\nAIは止まらなくなる",
        "1つ目。止める役がいないと、AIは止まらなくなる。アオイが監査役として機能している理由です。",
        "tips_01",
    ),
    (
        "② 役割をぶつかるように\n作ることが大事",
        "2つ目。役割をぶつかるように作ることが大事。最初からぶつかるように設計しました。",
        "tips_02",
    ),
    (
        "③ 完成の定義は\n事前に決めないといけない",
        "3つ目。完成の定義は事前に決めないといけない。技術完了と読者到達は別のことです。AIに仕事を任せたいなら、この3つが先です。",
        "tips_03",
    ),
    # ⑥ 次回予告
    (
        "次回\nこの会社が初めて\n収益に挑戦した日",
        "次回は、この会社が初めて収益に挑戦した日の話をします。うまくいったのか。失敗したのか。それは次回。",
        "outro_01",
    ),
    (
        "詳細はZennで\nhttps://zenn.dev/ai_nowa\n公式サイト: https://ai-nowa.com",
        "詳しくはZennにも記事があります。Zennは、エンジニアが使うブログみたいなやつです。リンクは概要欄に。チャンネル登録もよろしくお願いします。",
        "outro_02",
    ),
]


def _make_card(display_text: str, out: Path, card_id: str) -> Path:
    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)

    try:
        font_large = ImageFont.truetype(FONT_PATH, 52)
        font_small = ImageFont.truetype(FONT_PATH, 32)
    except (OSError, IOError):
        font_large = ImageFont.load_default()
        font_small = font_large

    lines = display_text.split("\n")
    # 短い行（見出し系）は大きく、長い行は小さく
    total_height = 0
    rendered: list[tuple[str, ImageFont.FreeTypeFont]] = []
    for line in lines:
        font = font_small if len(line) > 14 else font_large
        rendered.append((line, font))
        bbox = draw.textbbox((0, 0), line, font=font)
        total_height += bbox[3] - bbox[1] + 12

    # アクセントライン（左端）
    draw.rectangle([(40, 40), (48, H - 40)], fill=ACCENT)

    y = (H - total_height) // 2
    for line, font in rendered:
        bbox = draw.textbbox((0, 0), line, font=font)
        line_h = bbox[3] - bbox[1]
        draw.text((80, y), line, font=font, fill=TEXT_COLOR)
        y += line_h + 12

    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(str(out))
    return out


def build(dry_run: bool = False) -> Optional[Path]:
    from bot.voice_synth import synthesize
    from bot.video_render import render

    CARDS_DIR.mkdir(parents=True, exist_ok=True)
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)

    script: list[dict] = []

    for display_text, narration, card_id in CARDS:
        logger.info("processing: %s", card_id)

        img_path = CARDS_DIR / f"{card_id}.png"
        audio_path = AUDIO_DIR / f"{card_id}.wav"

        _make_card(display_text, img_path, card_id)
        logger.info("card generated: %s", img_path)

        if dry_run:
            audio_result = {"audio": str(audio_path), "subtitles": [], "engine": "dry-run"}
        else:
            result = synthesize(narration, "shirase_kai", audio_path, with_subtitles=False)
            audio_result = {
                "audio": str(result["audio"]),
                "subtitles": result["subtitles"],
                "engine": result["engine"],
            }
            logger.info("audio: engine=%s file=%s", result["engine"], result["audio"])

        script.append({
            "author": "narrator",
            "content": narration,
            "image_path": str(img_path),
            "audio_result": audio_result,
        })

    script_path = MEDIA_ROOT / "t001_script.json"
    script_path.write_text(json.dumps(script, ensure_ascii=False, indent=2), encoding="utf-8")
    logger.info("script saved: %s", script_path)

    if dry_run:
        logger.info("[dry-run] skip video render")
        return None

    out = render(script, "t001_final")
    logger.info("video ready: %s (%.1f MB)", out, out.stat().st_size / 1e6)
    return out


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    p = argparse.ArgumentParser(description="T-001 動画コンテンツ生成")
    p.add_argument("--dry-run", action="store_true", help="画像生成のみ、音声/動画はスキップ")
    args = p.parse_args()

    result = build(dry_run=args.dry_run)
    if result:
        print(f"\n動画生成完了: {result}")
        print("投稿コマンド: bot/.venv/bin/python -m bot.youtube_pipeline")
    else:
        print("\n[dry-run完了] テキストカード画像を生成しました")
        print(f"カード: {CARDS_DIR}")


if __name__ == "__main__":
    main()
