"""thumbnail_gen.py - YouTube サムネイル生成 (Phase 1 / Day 4)

T-024 実績サムネイル（Discord 風 + 衝撃テロップ型）を bot モジュールとして再実装。
依存: Pillow のみ (CPU・無人実行)。

CLI:
    python -m bot.thumbnail_gen "テキスト" employee_id [--image path] [--out path]
"""
from __future__ import annotations

import argparse
import time
from pathlib import Path
from typing import Optional

from PIL import Image, ImageDraw, ImageFilter, ImageFont

FONT_PATH = "/home/ikuto/.local/share/fonts/NotoSansJP.ttf"

MEDIA_ROOT = Path(__file__).parent.parent / "shared" / "media"
THUMB_OUT = MEDIA_ROOT / "thumbnails"

W, H = 1280, 720

# Discord カラー
_SIDEBAR_BG = (32, 34, 37)
_CH_BG = (47, 49, 54)
_CHAT_BG = (54, 57, 63)
_TEXT = (220, 221, 222)
_MUTED = (163, 166, 170)
_ACCENT_RED = (230, 57, 70)

EMPLOYEE_COLORS: dict[str, str] = {
    "有馬レイジ": "#FF6B6B",
    "三枝ミオ":   "#F9CA24",
    "白瀬カイ":   "#4ECDC4",
    "朝倉ノア":   "#45B7D1",
    "星野リツ":   "#96E6A1",
    "黒羽ユウ":   "#F0932B",
    "神楽アオイ": "#6C5CE7",
    "森永ハル":   "#FD79A8",
    "日向ナギ":   "#74B9FF",
}

_SAMPLE_MESSAGES = [
    ("有馬レイジ", "今週のフェーズAを開始する。全員、準備はいいか？"),
    ("白瀬カイ",   "実装完了です。PR出しました。"),
    ("朝倉ノア",   "スコープ確認します。まず最小単位から。"),
    ("星野リツ",   "第1回台本、初稿仕上げました。"),
    ("三枝ミオ",   "スケジュール調整完了。5/20公開で進めます。"),
    ("黒羽ユウ",   "サムネA案、インパクト出ます。いきましょう。"),
    ("神楽アオイ", "監査クリア。炎上リスクなし。"),
    ("森永ハル",   "皆さんお疲れ様です。休憩も大切に。"),
    ("日向ナギ",   "初見でも伝わりました。「全員AI」は刺さる。"),
]


def _load_font(size: int) -> ImageFont.FreeTypeFont:
    try:
        return ImageFont.truetype(FONT_PATH, size)
    except OSError:
        return ImageFont.load_default()


def _hex_rgb(hex_color: str) -> tuple[int, int, int]:
    h = hex_color.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def _draw_discord_chrome(draw: ImageDraw.ImageDraw, img: Image.Image) -> None:
    draw.rectangle([0, 0, 60, H], fill=_SIDEBAR_BG)
    draw.rectangle([60, 0, 240, H], fill=_CH_BG)
    draw.rectangle([240, 0, W, H], fill=_CHAT_BG)

    for i, color in enumerate(["#FF6B6B", "#4ECDC4", "#96E6A1"]):
        y = 16 + i * 56
        draw.ellipse([8, y, 52, y + 44], fill=_hex_rgb(color) + (200,))

    f_sm = _load_font(13)
    draw.text((68, 12), "AI NOWA", fill=(255, 255, 255), font=_load_font(14))
    for i, ch in enumerate(["# 全体アナウンス", "# 開発部", "# 成果物報告", "# いくと依頼"]):
        draw.text((68, 48 + i * 28), ch, fill=_MUTED, font=f_sm)

    draw.rectangle([240, 0, W, 48], fill=_CH_BG)
    draw.text((260, 14), "# 開発部", fill=_TEXT, font=_load_font(16))
    draw.line([(240, 48), (W, 48)], fill=_SIDEBAR_BG, width=1)


def _draw_messages(draw: ImageDraw.ImageDraw) -> None:
    f_name = _load_font(14)
    f_msg = _load_font(13)
    f_time = _load_font(11)
    x, y0, lh = 260, 60, 52

    for i, (name, text) in enumerate(_SAMPLE_MESSAGES):
        y = y0 + i * lh
        color = _hex_rgb(EMPLOYEE_COLORS.get(name, "#5865F2"))
        draw.ellipse([x - 40, y, x - 10, y + 30], fill=color)
        draw.text((x, y), name, fill=color, font=f_name)
        nw = draw.textbbox((0, 0), name, font=f_name)[2]
        draw.text((x + nw + 8, y + 2), f"今日 {9 + i}:{i * 5:02d}", fill=_MUTED, font=f_time)
        draw.text((x, y + 18), text, fill=(200, 201, 202), font=f_msg)


def _draw_terop(draw: ImageDraw.ImageDraw, img: Image.Image, text: str) -> None:
    font = _load_font(14)
    for fsize in range(140, 50, -4):
        font = _load_font(fsize)
        bbox = draw.textbbox((0, 0), text, font=font)
        if bbox[2] - bbox[0] <= W * 0.45:
            break

    bbox = draw.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    tx, ty = W - tw - 40, 70

    for dx in range(-5, 6, 2):
        for dy in range(-5, 6, 2):
            if dx == 0 and dy == 0:
                continue
            draw.text((tx + dx, ty + dy), text, fill=(0, 0, 0), font=font)
    draw.text((tx, ty), text, fill=_ACCENT_RED, font=font)


def render(
    terop_text: str,
    employee_id: str,
    bg_image: Optional[Path] = None,
    out_path: Optional[Path] = None,
) -> Path:
    if out_path is None:
        THUMB_OUT.mkdir(parents=True, exist_ok=True)
        ts = int(time.time())
        out_path = THUMB_OUT / f"{ts}_{employee_id}.png"
    else:
        out_path.parent.mkdir(parents=True, exist_ok=True)

    if bg_image and bg_image.exists():
        img = Image.open(bg_image).convert("RGBA").resize((W, H))
    else:
        img = Image.new("RGBA", (W, H), _CHAT_BG)

    draw = ImageDraw.Draw(img)
    _draw_discord_chrome(draw, img)
    _draw_messages(draw)

    # チャンネルサイドバーをぼかしてプライバシー保護
    sidebar = img.crop((60, 0, 240, H))
    img.paste(sidebar.filter(ImageFilter.GaussianBlur(radius=10)), (60, 0))

    # 半透明オーバーレイ（テロップを目立たせる）
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 120))
    img.paste(overlay, (0, 0), overlay)

    draw = ImageDraw.Draw(img)
    _draw_terop(draw, img, terop_text)

    # ロゴ・キャプション
    draw.text((30, H - 80), "AI NOWA", fill=(255, 255, 255), font=_load_font(32))
    draw.text((30, H - 42), "AIが動かす会社", fill=(200, 200, 200), font=_load_font(16))
    cap = "9社員・Discord自律運営"
    cap_w = draw.textbbox((0, 0), cap, font=_load_font(18))[2]
    draw.text((W - cap_w - 30, H - 50), cap, fill=(255, 255, 255), font=_load_font(18))

    img.convert("RGB").save(str(out_path), "PNG")
    return out_path


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("terop_text", help="サムネイルに表示するテロップ文字列")
    p.add_argument("employee_id", help="担当社員ID（ファイル名に使用）")
    p.add_argument("--image", type=Path, help="背景画像パス（省略時はDiscord風デフォルト）")
    p.add_argument("--out", type=Path, help="出力先PNGパス（省略時は shared/media/thumbnails/ 以下）")
    args = p.parse_args()

    out = render(
        terop_text=args.terop_text,
        employee_id=args.employee_id,
        bg_image=args.image,
        out_path=args.out,
    )
    print(f"wrote: {out}  ({out.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
