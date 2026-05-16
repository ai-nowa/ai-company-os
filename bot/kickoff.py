"""AI NOWA 自律運営フェーズ キックオフ（Phase 2.7 マルチクライアント対応）。
- Architect Claude は メイン bot として 📢お知らせ に投稿
- 各社員はその社員 bot として該当チャンネルに投稿
"""
from __future__ import annotations

import logging
from typing import Optional

import discord

from .architect import run_architect
from . import multi_client
from .employee_runner import run_employee

log = logging.getLogger("kickoff")


async def find_channel(main_client: discord.Client, needle: str) -> Optional[discord.TextChannel]:
    for guild in main_client.guilds:
        for ch in guild.channels:
            if isinstance(ch, discord.TextChannel) and needle in ch.name:
                return ch
    return None


async def post_as_main(channel: Optional[discord.TextChannel], header: str, text: str) -> None:
    """メイン bot として投稿。bot 名そのものが表示されるためプレフィックスは付けない。"""
    if channel is None:
        log.warning(f"channel not found for header={header}")
        return
    chunks = [text[i:i + 1900] for i in range(0, len(text), 1900)] or ["(空)"]
    for chunk in chunks:
        await channel.send(chunk)


async def post_as_employee(emp_id: str, channel_needle: str, text: str) -> bool:
    ch = await multi_client.find_channel_for_employee(emp_id, channel_needle)
    if ch is None:
        log.warning(f"channel '{channel_needle}' not visible to {emp_id}")
        return False
    chunks = [text[i:i + 1900] for i in range(0, len(text), 1900)] or ["(空)"]
    for chunk in chunks:
        await ch.send(chunk)
    return True


async def kickoff(main_client: discord.Client) -> None:
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
    notice_ch = await find_channel(main_client, "お知らせ")
    await post_as_main(notice_ch, "設計者（Opus）", archi_msg)

    log.info("Step 2/3: レイジ社長が方針発表を作成...")
    reiji_msg = await run_employee(
        "arima_reiji",
        "AI NOWA が始動した。会社のミッション（mission.md）をあなたは既に読んでいる前提です。"
        "あなたはCEOとして、📢お知らせチャンネル向けに「今日からの方針」を社員に宣言してください。"
        "あなたの口癖と人格を保ったまま、5〜10行で。"
        "「今日、何を出荷する？」をどう適用するか、自律運営をどう始めるかを含めて。"
        "@三枝ミオ に事業判断トライアドの招集を依頼することも宣言してください（必ず @ を付けて）。",
        sender="いくと",
    )
    await post_as_employee("arima_reiji", "お知らせ", reiji_msg)

    log.info("Step 3/3: ミオ COO が事業判断トライアド招集...")
    mio_msg = await run_employee(
        "saegusa_mio",
        "レイジ社長が会社始動方針を発表しました。"
        "あなたは事業判断トライアド（レイジ・ミオ・ノア）を招集して、"
        "最初の収益化チャネルを決める議論を🎯経営会議で始めてください。"
        "あなたの口癖と整理力を保ったまま、3〜5行で:"
        "(1) 議論の論点を3つに絞る、"
        "(2) @有馬レイジ と @朝倉ノア に開始を呼びかける（@ 必須）、"
        "(3) 期限の目安を提案する。",
        sender="いくと",
    )
    await post_as_employee("saegusa_mio", "経営会議", mio_msg)

    # ミオの応答に含まれる @メンションから連鎖発火（in-process）
    try:
        from .dispatcher import process_mention_chain
        biz_ch = await find_channel(main_client, "経営会議")
        if biz_ch is not None:
            log.info("ミオ応答からの連鎖発火開始")
            await process_mention_chain(
                mio_msg, "saegusa_mio", biz_ch,
                depth=0, visited={"saegusa_mio"},
            )
    except Exception:
        log.exception("連鎖発火失敗（kickoff は完了扱い）")

    log.info("✓ kickoff complete")


def main() -> None:
    """単独 CLI 実行用（dispatcher 経由ではない場合）"""
    import asyncio
    from .config import DISCORD_BOT_TOKEN

    if not DISCORD_BOT_TOKEN:
        raise RuntimeError("DISCORD_BOT_TOKEN 未設定")
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

    intents = discord.Intents.default()
    intents.message_content = True
    main_client = discord.Client(intents=intents)

    @main_client.event
    async def on_ready() -> None:
        log.info(f"Logged in as {main_client.user}")
        await multi_client.start_all(intents)
        try:
            await kickoff(main_client)
        except Exception:
            log.exception("kickoff failed")
        finally:
            await multi_client.stop_all()
            await main_client.close()

    main_client.run(DISCORD_BOT_TOKEN)


if __name__ == "__main__":
    main()
