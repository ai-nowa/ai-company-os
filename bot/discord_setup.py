"""Discord サーバー初期化スクリプト。

bot をサーバーに招待した後、このスクリプトを実行すると
`company/discord_channels.md` の構成に従ってカテゴリ・チャンネル・ロールを
自動作成する。冪等に動くため、既存と同名のものはスキップする。

使い方:
    # bot招待後（DISCORD_BOT_TOKEN は .env から読む）
    python -m bot.discord_setup --guild <GUILD_ID>

    # GUILD_ID が分からない時は bot が参加中のサーバー一覧を表示
    python -m bot.discord_setup --list-guilds
"""
from __future__ import annotations

import argparse
import asyncio
import logging
import sys

import discord

from .config import DISCORD_BOT_TOKEN

log = logging.getLogger("discord_setup")

# discord_channels.md と対応した構造定義
CATEGORIES: list[dict] = [
    {
        "name": "📣全社",
        "channels": [
            "📢｜お知らせ",
            "🏢｜会社案内",
            "👀｜見学者向けガイド",
            "🗓｜今日の業務",
            "🧾｜議事録",
        ],
    },
    {
        "name": "🏛会議",
        "channels": [
            "🏛｜全社会議",
            "🎯｜経営会議",
            "🧩｜プロダクト会議",
        ],
    },
    {
        "name": "🛠部署",
        "channels": [
            "🛠｜開発部",
            "🎬｜youtube編集部",
            "📈｜マーケ部",
            "⚖｜監査部",
        ],
    },
    {
        "name": "🌱文化",
        "channels": [
            "☕｜給湯室-雑談",
            "🌱｜well-being",
            "👏｜ありがとう-称賛",
            "🧯｜モヤモヤ相談",
            "🔁｜ふりかえり",
            "🧠｜ひらめきメモ",
            "📦｜成果物報告",
        ],
    },
]

ROLES: list[dict] = [
    {"name": "オーナー", "color": discord.Color.gold(),  "hoist": True},
    {"name": "bot",     "color": discord.Color.blue(),  "hoist": False},
    {"name": "見学者",   "color": discord.Color.dark_grey(), "hoist": False},
]


async def setup_guild(client: discord.Client, guild_id: int) -> None:
    guild = client.get_guild(guild_id)
    if guild is None:
        log.error(f"Guild not found: {guild_id}（botが参加していますか？）")
        return

    log.info(f"Setting up: {guild.name} ({guild.id})")

    # ロール作成（既存はスキップ）
    existing_roles = {r.name for r in guild.roles}
    for role_def in ROLES:
        if role_def["name"] in existing_roles:
            log.info(f"  role exists: {role_def['name']}")
            continue
        await guild.create_role(
            name=role_def["name"],
            color=role_def["color"],
            hoist=role_def["hoist"],
            mentionable=True,
            reason="AI Company OS initial setup",
        )
        log.info(f"  + role: {role_def['name']}")

    # カテゴリ + チャンネル作成
    existing_categories = {c.name: c for c in guild.categories}
    existing_channels = {c.name for c in guild.channels}

    for cat_def in CATEGORIES:
        cat = existing_categories.get(cat_def["name"])
        if cat is None:
            cat = await guild.create_category(cat_def["name"], reason="AI Company OS setup")
            log.info(f"  + category: {cat_def['name']}")
        else:
            log.info(f"  category exists: {cat_def['name']}")

        for ch_name in cat_def["channels"]:
            if ch_name in existing_channels:
                log.info(f"    channel exists: {ch_name}")
                continue
            await guild.create_text_channel(ch_name, category=cat, reason="AI Company OS setup")
            log.info(f"    + channel: {ch_name}")

    log.info("Setup completed ✓")


async def list_guilds(client: discord.Client) -> None:
    log.info("Bot が参加中のサーバー一覧:")
    for g in client.guilds:
        log.info(f"  {g.id} - {g.name}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Discord サーバー初期化")
    parser.add_argument("--guild", type=int, help="セットアップ対象の Guild ID")
    parser.add_argument("--list-guilds", action="store_true", help="参加中サーバー一覧を表示")
    args = parser.parse_args()

    if not DISCORD_BOT_TOKEN:
        print("DISCORD_BOT_TOKEN が未設定 (.env を確認)", file=sys.stderr)
        sys.exit(1)
    if not args.guild and not args.list_guilds:
        parser.error("--guild <ID> か --list-guilds を指定してください")

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    intents = discord.Intents.default()
    intents.guilds = True
    client = discord.Client(intents=intents)

    @client.event
    async def on_ready() -> None:
        try:
            if args.list_guilds:
                await list_guilds(client)
            else:
                await setup_guild(client, args.guild)
        finally:
            await client.close()

    client.run(DISCORD_BOT_TOKEN)


if __name__ == "__main__":
    main()
