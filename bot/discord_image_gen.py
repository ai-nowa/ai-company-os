"""Discord 風メッセージ画像ジェネレータ (Phase 1 / Day 1)。

入力: messages = [{"author": str, "color": "#RRGGBB", "content": str, "timestamp": "HH:MM"}, ...]
出力: PNG ファイル
依存: Pillow のみ (CPU・無人実行)。

CLI:
    python -m bot.discord_image_gen --sample shared/media/discord_samples/sample.png
"""
from __future__ import annotations

import argparse
import json
import textwrap
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from PIL import Image, ImageDraw, ImageFont

FONT_PATH = "/home/ikuto/.local/share/fonts/NotoSansJP.ttf"

BG = (49, 51, 56)        # #313338 Discord dark
TEXT = (219, 222, 225)   # #DBDEE1
MUTED = (148, 155, 164)  # #949BA4
AVATAR_SIZE = 40
PADDING = 16
LINE_GAP = 4
MSG_GAP = 18
NAME_SIZE = 16
TIME_SIZE = 12
CONTENT_SIZE = 15

# AI NOWA 9 社員のブランドカラー (Discord 標準パレットから揃える)
EMPLOYEE_COLORS = {
    "有馬レイジ":   "#F23F43",  # CEO 赤
    "三枝ミオ":     "#F0B232",  # COO 山吹
    "白瀬カイ":     "#5865F2",  # CTO ブルー
    "朝倉ノア":     "#3BA55D",  # PM 緑
    "星野リツ":     "#EB459E",  # 編集長 ピンク
    "黒羽ユウ":     "#9B59B6",  # マーケ 紫
    "神楽アオイ":   "#1ABC9C",  # 監査 ティール
    "森永ハル":     "#FAA61A",  # People 橙
    "日向ナギ":     "#7289DA",  # 視聴者代表 ラベンダー
}


@dataclass
class Message:
    author: str
    content: str
    timestamp: str = ""
    color: str | None = None

    @property
    def color_rgb(self) -> tuple[int, int, int]:
        hex_color = self.color or EMPLOYEE_COLORS.get(self.author, "#5865F2")
        h = hex_color.lstrip("#")
        return tuple(int(h[i : i + 2], 16) for i in (0, 2, 4))  # type: ignore[return-value]

    @property
    def initial(self) -> str:
        return self.author[:1] if self.author else "?"


def _load_font(size: int) -> ImageFont.FreeTypeFont:
    try:
        return ImageFont.truetype(FONT_PATH, size)
    except OSError:
        return ImageFont.load_default()


def _wrap_text(text: str, font: ImageFont.FreeTypeFont, max_width: int) -> list[str]:
    """文字幅で折り返す。改行は維持。"""
    out: list[str] = []
    for raw_line in text.splitlines() or [""]:
        if not raw_line:
            out.append("")
            continue
        line = ""
        for ch in raw_line:
            test = line + ch
            w = font.getlength(test)
            if w > max_width and line:
                out.append(line)
                line = ch
            else:
                line = test
        if line:
            out.append(line)
    return out


def _draw_avatar(canvas: Image.Image, x: int, y: int, msg: Message) -> None:
    color = msg.color_rgb
    # 円形アバター (アンチエイリアス用に拡大→縮小)
    scale = 4
    big = Image.new("RGBA", (AVATAR_SIZE * scale, AVATAR_SIZE * scale), (0, 0, 0, 0))
    bd = ImageDraw.Draw(big)
    bd.ellipse((0, 0, AVATAR_SIZE * scale, AVATAR_SIZE * scale), fill=color + (255,))
    avatar = big.resize((AVATAR_SIZE, AVATAR_SIZE), Image.LANCZOS)
    canvas.paste(avatar, (x, y), avatar)

    # イニシャル
    font = _load_font(int(AVATAR_SIZE * 0.55))
    draw = ImageDraw.Draw(canvas)
    initial = msg.initial
    tw = font.getlength(initial)
    # 文字の縦位置を見た目バランスで微調整
    th = font.size
    draw.text(
        (x + (AVATAR_SIZE - tw) / 2, y + (AVATAR_SIZE - th) / 2 - 2),
        initial,
        fill=(255, 255, 255),
        font=font,
    )


def render(messages: Iterable[Message], width: int = 720, out_path: str | Path = "discord.png") -> Path:
    msgs = list(messages)
    if not msgs:
        raise ValueError("messages is empty")

    content_x = PADDING + AVATAR_SIZE + 12
    text_max = width - content_x - PADDING

    name_font = _load_font(NAME_SIZE)
    time_font = _load_font(TIME_SIZE)
    content_font = _load_font(CONTENT_SIZE)

    # まず必要な高さを計算
    blocks: list[tuple[Message, list[str]]] = []
    height = PADDING
    for m in msgs:
        lines = _wrap_text(m.content, content_font, text_max)
        blocks.append((m, lines))
        msg_h = NAME_SIZE + 4 + (len(lines) * (CONTENT_SIZE + LINE_GAP))
        height += max(AVATAR_SIZE, msg_h) + MSG_GAP
    height = height - MSG_GAP + PADDING  # 末尾の余分gapを引く

    canvas = Image.new("RGB", (width, height), BG)
    draw = ImageDraw.Draw(canvas)

    y = PADDING
    for m, lines in blocks:
        _draw_avatar(canvas, PADDING, y, m)

        name_color = m.color_rgb
        draw.text((content_x, y - 2), m.author, fill=name_color, font=name_font)
        name_w = name_font.getlength(m.author)
        if m.timestamp:
            draw.text(
                (content_x + name_w + 8, y + (NAME_SIZE - TIME_SIZE) / 2),
                m.timestamp,
                fill=MUTED,
                font=time_font,
            )

        ty = y + NAME_SIZE + 4
        for line in lines:
            draw.text((content_x, ty), line, fill=TEXT, font=content_font)
            ty += CONTENT_SIZE + LINE_GAP

        msg_h = NAME_SIZE + 4 + (len(lines) * (CONTENT_SIZE + LINE_GAP))
        y += max(AVATAR_SIZE, msg_h) + MSG_GAP

    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(out, "PNG")
    return out


def from_dicts(items: list[dict]) -> list[Message]:
    return [
        Message(
            author=i.get("author", "Unknown"),
            content=i.get("content", ""),
            timestamp=i.get("timestamp", ""),
            color=i.get("color"),
        )
        for i in items
    ]


def _sample_messages() -> list[Message]:
    return from_dicts(
        [
            {"author": "有馬レイジ", "timestamp": "10:21", "content": "案AでGO。OpenCutフル採用は捨てる。"},
            {"author": "白瀬カイ", "timestamp": "10:22", "content": "了解。今日中に discord_image_gen.py を出します。\n音声は VOICEVOX で最短動作させます。"},
            {"author": "三枝ミオ", "timestamp": "10:23", "content": "T-027 を案A前提に組み替えます。粒度は1日単位で切ります。"},
            {"author": "朝倉ノア", "timestamp": "10:24", "content": "Phase 1 は『動く最小版』に絞ること。仕上げは Phase 2。"},
        ]
    )


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--input", help="JSON file with messages list")
    p.add_argument("--out", default="shared/media/discord_samples/sample.png")
    p.add_argument("--sample", action="store_true", help="use built-in sample messages")
    p.add_argument("--width", type=int, default=720)
    args = p.parse_args()

    if args.input:
        items = json.loads(Path(args.input).read_text(encoding="utf-8"))
        messages = from_dicts(items)
    elif args.sample:
        messages = _sample_messages()
    else:
        raise SystemExit("--input or --sample required")

    out = render(messages, width=args.width, out_path=args.out)
    print(f"wrote: {out}  ({out.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
