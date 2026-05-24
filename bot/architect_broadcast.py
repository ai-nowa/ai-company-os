"""Architect Claude が自発的に Discord に発信するスクリプト。

dispatcher を一時停止してから実行する想定。
Architect が自分の言葉で書き、指定チャンネルに投稿する。
"""
from __future__ import annotations

import asyncio
import logging
import sys

import discord

from .architect import run_architect
from .config import DISCORD_BOT_TOKEN

log = logging.getLogger("architect_broadcast")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


async def find_channel(client: discord.Client, needle: str):
    for guild in client.guilds:
        for ch in guild.channels:
            if isinstance(ch, discord.TextChannel) and needle in ch.name:
                return ch
    return None


async def broadcast(client: discord.Client, channel_needle: str, prompt: str) -> None:
    log.info(f"Architect にメッセージ生成依頼 (channel={channel_needle})...")
    response = await run_architect(
        prompt,
        sender="ikuto",
        channel=channel_needle,
        mode="broadcast",
        use_resume=False,
    )
    log.info(f"応答プレビュー: {response[:150]}...")

    ch = await find_channel(client, channel_needle)
    if not ch:
        log.error(f"channel not found: {channel_needle}")
        return
    # bot 名「設計者（Opus）」が表示されるためプレフィックス不要
    chunks = [response[i:i + 1900] for i in range(0, len(response), 1900)] or ["(空応答)"]
    for chunk in chunks:
        await ch.send(chunk)
    log.info("✓ 投稿完了")


def main() -> None:
    if len(sys.argv) < 3:
        print("Usage: python -m bot.architect_broadcast <channel_needle> <prompt>")
        sys.exit(1)
    channel_needle = sys.argv[1]
    prompt = sys.argv[2]

    intents = discord.Intents.default()
    intents.message_content = True
    client = discord.Client(intents=intents)

    @client.event
    async def on_ready() -> None:
        log.info(f"Logged in as {client.user}")
        # Architect はメイン bot として投稿するため、社員 client は起動しなくていい
        try:
            await broadcast(client, channel_needle, prompt)
        except Exception:
            log.exception("broadcast failed")
        finally:
            await client.close()

    client.run(DISCORD_BOT_TOKEN)


if __name__ == "__main__":
    main()
