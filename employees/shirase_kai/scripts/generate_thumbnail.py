#!/usr/bin/env python3
"""T-024サムネイル生成: 「全員AIです」衝撃テロップ型"""

from PIL import Image, ImageDraw, ImageFont, ImageFilter
import os

FONT_PATH = "/home/ikuto/.local/share/fonts/NotoSansJP.ttf"
OUT_PATH = "/home/ikuto/ai-company-os/employees/shirase_kai/outbox/thumbnail_t024_v2.png"

W, H = 1280, 720

# Discord color scheme
DISCORD_BG = (54, 57, 63)        # #36393F
DISCORD_SIDEBAR = (47, 49, 54)   # #2F3136
DISCORD_CHAT_BG = (54, 57, 63)
DISCORD_MSG_BG = (64, 68, 75)    # hover color
DISCORD_TEXT = (220, 221, 222)   # #DCDDE
DISCORD_MUTED = (163, 166, 170)
DISCORD_ONLINE = (59, 165, 93)   # green dot
DISCORD_LINK = (0, 176, 244)

ACCENT_RED = (230, 57, 70)       # #E63946

# 社員名と発言サンプル
MESSAGES = [
    ("有馬レイジ", "#FF6B6B", "今週のフェーズAを開始する。全員、準備はいいか？", True),
    ("白瀬カイ", "#4ECDC4", "実装完了です。PR出しました。", False),
    ("朝倉ノア", "#45B7D1", "スコープ確認します。まず最小単位から。", False),
    ("星野リツ", "#96E6A1", "第1回台本、初稿仕上げました。", False),
    ("三枝ミオ", "#F9CA24", "スケジュール調整完了。5/20公開で進めます。", False),
    ("黒羽ユウ", "#F0932B", "サムネA案、インパクト出ます。いきましょう。", False),
    ("神楽アオイ", "#6C5CE7", "監査クリア。炎上リスクなし。", False),
    ("森永ハル", "#FD79A8", "皆さんお疲れ様です。休憩も大切に。", False),
    ("日向ナギ", "#74B9FF", "初見でも伝わりました。「全員AI」は刺さる。", False),
]


def load_font(size):
    return ImageFont.truetype(FONT_PATH, size)


def draw_discord_bg(draw, img):
    # サイドバー
    draw.rectangle([0, 0, 60, H], fill=(32, 34, 37))
    # チャンネルサイドバー
    draw.rectangle([60, 0, 240, H], fill=DISCORD_SIDEBAR)
    # メインチャット領域
    draw.rectangle([240, 0, W, H], fill=DISCORD_BG)

    # サイドバーアイコン風（サーバーアイコン）
    for i, (color_hint) in enumerate(["#FF6B6B", "#4ECDC4", "#96E6A1"]):
        y = 16 + i * 56
        r, g, b = int(color_hint[1:3], 16), int(color_hint[3:5], 16), int(color_hint[5:7], 16)
        draw.ellipse([8, y, 52, y + 44], fill=(r, g, b, 200))

    # チャンネルリスト
    font_sm = load_font(13)
    channels = ["# 全体アナウンス", "# 開発部", "# 成果物報告", "# いくと依頼"]
    draw.text((68, 12), "AI NOWA", fill=(255, 255, 255), font=load_font(14))
    for i, ch in enumerate(channels):
        y = 48 + i * 28
        draw.text((68, y), ch, fill=DISCORD_MUTED, font=font_sm)

    # チャンネルヘッダー
    draw.rectangle([240, 0, W, 48], fill=(47, 49, 54))
    draw.text((260, 14), "# 開発部", fill=DISCORD_TEXT, font=load_font(16))
    draw.line([(240, 48), (W, 48)], fill=(32, 34, 37), width=1)


def draw_messages(draw, img):
    font_name = load_font(14)
    font_msg = load_font(13)
    font_time = load_font(11)

    msg_x = 260
    start_y = 60
    line_h = 52

    for i, (name, color_hex, text, _) in enumerate(MESSAGES):
        y = start_y + i * line_h
        r = int(color_hex[1:3], 16)
        g = int(color_hex[3:5], 16)
        b = int(color_hex[5:7], 16)

        # アバター（小さい円）
        draw.ellipse([msg_x - 40, y, msg_x - 10, y + 30], fill=(r, g, b))

        # 名前
        draw.text((msg_x, y), name, fill=(r, g, b), font=font_name)
        # 時刻（名前幅をtextbboxで正確に計算）
        name_w = draw.textbbox((0, 0), name, font=font_name)[2]
        draw.text((msg_x + name_w + 8, y + 2), f"今日 {9 + i}:{i * 5:02d}", fill=DISCORD_MUTED, font=font_time)
        # 本文
        draw.text((msg_x, y + 18), text, fill=(200, 201, 202), font=font_msg)


def draw_overlay(draw, img):
    # 全体に軽い暗幕（テロップを目立たせる）
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 120))
    img.paste(overlay, (0, 0), overlay)


def draw_terop(draw, img):
    text = "全員AIです"
    # 右上配置なのでW*0.45に収める
    for fsize in range(140, 50, -4):
        f = load_font(fsize)
        bbox = draw.textbbox((0, 0), text, font=f)
        tw = bbox[2] - bbox[0]
        if tw <= W * 0.45:
            break

    th = bbox[3] - bbox[1]
    # 右上に配置（Discordログを隠さない）
    tx = W - tw - 40
    ty = 70

    # 縁取り（黒）
    for dx in range(-5, 6, 2):
        for dy in range(-5, 6, 2):
            if dx == 0 and dy == 0:
                continue
            draw.text((tx + dx, ty + dy), text, fill=(0, 0, 0), font=f)

    # メインテロップ（赤）
    draw.text((tx, ty), text, fill=ACCENT_RED, font=f)


def draw_logo(draw):
    # 左下: AI NOWAロゴ風テキスト
    font_logo = load_font(32)
    font_sub = load_font(16)
    draw.text((30, H - 80), "AI NOWA", fill=(255, 255, 255), font=font_logo)
    draw.text((30, H - 42), "AIが動かす会社", fill=(200, 200, 200), font=font_sub)


def draw_caption(draw):
    # 右下: 9社員・Discord自律運営
    font_cap = load_font(18)
    text = "9社員・Discord自律運営"
    bbox = draw.textbbox((0, 0), text, font=font_cap)
    tw = bbox[2] - bbox[0]
    draw.text((W - tw - 30, H - 50), text, fill=(255, 255, 255), font=font_cap)


def main():
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)

    img = Image.new("RGBA", (W, H), DISCORD_BG)
    draw = ImageDraw.Draw(img)

    draw_discord_bg(draw, img)
    draw_messages(draw, img)

    # サイドバーにぼかしをかけて「いくと依頼」文字を読めなくする
    sidebar = img.crop((60, 0, 240, H))
    img.paste(sidebar.filter(ImageFilter.GaussianBlur(radius=10)), (60, 0))

    draw_overlay(draw, img)

    draw = ImageDraw.Draw(img)  # overlay paste後に再取得
    draw_terop(draw, img)
    draw_logo(draw)
    draw_caption(draw)

    img = img.convert("RGB")
    img.save(OUT_PATH, "PNG", quality=95)
    print(f"Generated: {OUT_PATH}")


if __name__ == "__main__":
    main()
