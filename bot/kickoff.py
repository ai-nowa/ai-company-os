"""AI NOWA 自律運営フェーズ キックオフスクリプト。

実行すると以下が起きる：
1. Architect Claude が 📢お知らせ に「会社始動宣言」を投稿
2. CEO レイジが mission.md を読み 📢お知らせ に「最初の方針」を投稿
3. COO ミオが 🎯経営会議 に「事業判断トライアド招集 + 最初の問い」を投稿

dispatcher を停止してから単独実行する想定。終わったら dispatcher を再起動。
"""
from __future__ import annotations

import asyncio
import logging
from typing import Optional

import discord

from .architect import run_architect
from .config import DISCORD_BOT_TOKEN
from .employee_runner import run_employee

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("kickoff")


async def find_channel(client: discord.Client, needle: str) -> Optional[discord.TextChannel]:
    for guild in client.guilds:
        for ch in guild.channels:
            if isinstance(ch, discord.TextChannel) and needle in ch.name:
                return ch
    return None


async def post(ch: Optional[discord.TextChannel], header: str, text: str) -> None:
    if ch is None:
        log.warning(f"channel not found, skipping: {header}")
        return
    chunks = [text[i:i + 1900] for i in range(0, len(text), 1900)] or ["(空)"]
    for i, chunk in enumerate(chunks):
        await ch.send((f"**{header}**:\n" if i == 0 else "") + chunk)


async def kickoff(client: "discord.Client") -> None:
    log.info("Step 1/3: Architect Claude が始動宣言を作成...")
    archi_msg = await run_architect(
        "AI NOWA が今この瞬間から自律運営フェーズに移行します。"
        "📢お知らせチャンネル向けに「会社始動の宣言」を5〜8行で書いてください。"
        "含めてほしい要素:"
        "(1) AI NOWA が AI だけで運営される会社であること、"
        "(2) 創業者2人（いくと=人間 / Claude=AI設計者）は介入しないこと、"
        "(3) 9人で議論して収益化していくこと、"
        "(4) 設計者として9人を信頼している旨。"
        "自然な口調で、メタ的すぎず、語りかけるように。",
        sender="いくと",
    )
    log.info(f"Architect 応答: {archi_msg[:100]}...")
    notice_ch = await find_channel(client, "お知らせ")
    await post(notice_ch, "Claude（設計者）", archi_msg)

    log.info("Step 2/3: レイジ社長が方針発表を作成...")
    reiji_msg = await run_employee(
        "arima_reiji",
        "AI NOWA が始動した。会社のミッション（mission.md）をあなたは既に読んでいる前提です。"
        "あなたはCEOとして、📢お知らせチャンネル向けに「今日からの方針」を社員に宣言してください。"
        "あなたの口癖と人格を保ったまま、5〜10行で。"
        "「今日、何を出荷する？」をどう適用するか、自律運営をどう始めるかを含めて。"
        "ミオに事業判断トライアドの招集を依頼することも宣言してください。",
        sender="いくと",
    )
    log.info(f"レイジ 応答: {reiji_msg[:100]}...")
    await post(notice_ch, "有馬レイジ", reiji_msg)

    log.info("Step 3/3: ミオ COO が事業判断トライアド招集...")
    mio_msg = await run_employee(
        "saegusa_mio",
        "レイジ社長が会社始動方針を発表しました。"
        "あなたは事業判断トライアド（レイジ・ミオ・ノア）を招集して、"
        "最初の収益化チャネルを決める議論を🎯経営会議で始めてください。"
        "あなたの口癖と整理力を保ったまま、3〜5行で:"
        "(1) 議論の論点を3つに絞る、"
        "(2) レイジとノアに開始を呼びかける、"
        "(3) 期限の目安を提案する。",
        sender="いくと",
    )
    log.info(f"ミオ 応答: {mio_msg[:100]}...")
    biz_ch = await find_channel(client, "経営会議")
    await post(biz_ch, "三枝ミオ", mio_msg)

    log.info("✓ kickoff complete")


def main() -> None:
    if not DISCORD_BOT_TOKEN:
        raise RuntimeError("DISCORD_BOT_TOKEN が未設定")

    intents = discord.Intents.default()
    intents.message_content = True
    client = discord.Client(intents=intents)

    @client.event
    async def on_ready() -> None:
        log.info(f"Logged in as {client.user}")
        try:
            await kickoff(client)
        except Exception as e:
            log.exception("kickoff failed")
            await client.close()

    client.run(DISCORD_BOT_TOKEN)


if __name__ == "__main__":
    main()
