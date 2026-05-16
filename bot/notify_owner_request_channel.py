"""いくと依頼チャンネル開設を全社員に通知 + レイジに過去の依頼整理を指示。

Architect が全社員に向けて通知し、レイジに具体的なアクションを振る一発スクリプト。
dispatcher 動作中でも別 token を使わず、bot 経由で投稿する。
"""
from __future__ import annotations

import asyncio
import logging
import sys

import discord

from .config import DISCORD_BOT_TOKEN
from . import multi_client
from .architect import run_architect
from .employee_runner import run_employee

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("notify_owner_req")


async def find_channel(client: discord.Client, needle: str):
    for guild in client.guilds:
        for ch in guild.channels:
            if isinstance(ch, discord.TextChannel) and needle in ch.name:
                return ch
    return None


async def run(client: discord.Client) -> None:
    """dispatcher の main_client を流用して通知を投稿（別 client を立てない、token 衝突回避）"""
    log.info("Step 1: Architect が📢お知らせに通知を作成...")
    archi_msg = await run_architect(
        "📥いくと依頼チャンネルが新規開設されました。"
        "📢お知らせチャンネル向けに全社員への通知を5〜8行で書いてください。"
        "(1) 専用チャンネル『📥いくと依頼』が開設された "
        "(2) 今後いくとへの依頼はそこに集約する "
        "(3) `company/owner_request_protocol.md` のテンプレ必須（タイトル/なぜ/詳細手順/期待結果/完了時報告先/緊急度/起票者） "
        "(4) 過去に他のチャンネルに散在していた依頼があれば、起票者が各自そこに移動・整理せよ "
        "(5) 監査（神楽アオイ）はテンプレ違反を見つけたら即指摘する "
        "短く、設計者の落ち着いた口調で。",
        sender="watchdog",
    )
    notice_ch = await find_channel(client, "お知らせ")
    if notice_ch:
        chunks = [archi_msg[i:i + 1900] for i in range(0, len(archi_msg), 1900)] or ["(空)"]
        for chunk in chunks:
            await notice_ch.send(chunk)
        log.info("✓ Architect 通知投稿完了")
    else:
        log.warning("お知らせチャンネルが見つかりません")

    log.info("Step 2: レイジに過去の依頼整理を指示...")
    reiji_msg = await run_employee(
        "arima_reiji",
        "📥いくと依頼チャンネルが開設された。設計者からの全社通知が📢お知らせに出ている。"
        "あなたが CEO として、これまでに私（いくと）に振りたかった依頼があれば、"
        "owner_request_protocol.md のテンプレに従って整理し、📥いくと依頼チャンネルに投稿してください。\n\n"
        "応答内に POST ブロックを使う:\n"
        "[POST: いくと依頼]\n"
        "## 【依頼: タイトル】\n"
        "### なぜ必要か\n"
        "...\n"
        "### 詳細手順\n"
        "1. ...\n"
        "### 期待される結果\n"
        "### 完了時の報告先\n"
        "### 緊急度\n"
        "### 起票者\n"
        "@有馬レイジ\n"
        "[/POST]\n\n"
        "依頼が複数あれば、POST ブロックも複数書いて構わない。"
        "依頼が無ければ、その旨を📢お知らせで一言報告してから何もしないでOK。"
        "他の社員（@三枝ミオ、@朝倉ノア 等）にも振りたい依頼があるか確認したい場合、メンションで聞いてもよい。",
        sender="watchdog",
    )

    # レイジの応答から POST ブロックを抽出して投稿
    from .employee_autonomy import _post_blocks_and_chain
    await _post_blocks_and_chain("arima_reiji", reiji_msg, client)
    log.info("✓ レイジへの指示と応答処理完了")


def main() -> None:
    if not DISCORD_BOT_TOKEN:
        raise RuntimeError("DISCORD_BOT_TOKEN 未設定")

    intents = discord.Intents.default()
    intents.message_content = True
    client = discord.Client(intents=intents)

    @client.event
    async def on_ready():
        log.info(f"Logged in as {client.user}")
        await multi_client.start_all(intents)
        await multi_client.build_role_map_from(client)
        try:
            await run(client)
        except Exception:
            log.exception("notify failed")
        finally:
            await multi_client.stop_all()
            await client.close()

    client.run(DISCORD_BOT_TOKEN)


if __name__ == "__main__":
    main()
