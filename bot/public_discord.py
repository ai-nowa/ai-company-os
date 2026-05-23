"""公開Discord「水瓶」サーバーへの投稿ユーティリティ。

チャンネル構成（ユウ設計 v1）:
  #観察日記  — storyteller.py の discord_snippet を毎日投稿
  #今日の一言 — 社員の印象的な発言を1日1本ピックアップ
  #質問してみて — 外部からの質問受け付け（Phase B）

環境変数:
  PUBLIC_DISCORD_KANSATSU_WEBHOOK   — #観察日記 の Webhook URL
  PUBLIC_DISCORD_ICHIMON_WEBHOOK    — #今日の一言 の Webhook URL

Webhook は公開Discordサーバーのチャンネル設定 → 「連携サービス」→「Webhook作成」で取得。
いくとにセットアップを依頼中: employees/shirase_kai/outbox/2026-05-22_public_discord_webhook_setup.md
"""
from __future__ import annotations

import asyncio
import logging
import os
from pathlib import Path

import aiohttp
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env")

log = logging.getLogger(__name__)

ENV_KANSATSU = "PUBLIC_DISCORD_KANSATSU_WEBHOOK"
ENV_ICHIMON  = "PUBLIC_DISCORD_ICHIMON_WEBHOOK"


async def _post_webhook(webhook_url: str, content: str) -> bool:
    """Discord Webhook に content を送信する。成功で True を返す。"""
    if not webhook_url:
        log.warning("Webhook URL 未設定のため投稿をスキップ")
        return False
    if len(content) > 2000:
        content = content[:1997] + "..."

    async with aiohttp.ClientSession() as session:
        resp = await session.post(webhook_url, json={"content": content})
        if resp.status in (200, 204):
            return True
        body = await resp.text()
        log.error("Webhook POST 失敗 status=%d body=%s", resp.status, body[:200])
        return False


async def post_kansatsu_nikki(snippet: str) -> bool:
    """#観察日記 チャンネルに discord_snippet を投稿する。"""
    url = os.environ.get(ENV_KANSATSU, "")
    return await _post_webhook(url, snippet)


async def post_kyou_no_ichimon(content: str) -> bool:
    """#今日の一言 チャンネルにコンテンツを投稿する。"""
    url = os.environ.get(ENV_ICHIMON, "")
    return await _post_webhook(url, content)


def post_kansatsu_nikki_sync(snippet: str) -> bool:
    """同期ラッパー（スクリプト直呼び用）。"""
    return asyncio.run(post_kansatsu_nikki(snippet))
