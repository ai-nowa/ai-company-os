"""日次スケジューラ（Phase 2.7 マルチクライアント対応）。
各社員の自動投稿は その社員 bot として行う。
"""
from __future__ import annotations

import logging
from typing import Optional

import discord
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from .config import EMPLOYEES, JST, append_discord_log
from . import multi_client
from .employee_runner import run_employee
from .health_monitor import write_health_report

log = logging.getLogger("daily_loop")

CHANNEL_MATCH = {
    "today_business": "今日の業務",
    "wellbeing":      "well-being",
    "chat":           "給湯室",
    "thanks":         "ありがとう",
    "report":         "成果物報告",
}


async def post_as_employee(emp_id: str, channel_key: str, text: str) -> None:
    """指定社員 bot として、CHANNEL_MATCH で指定されたチャンネル名に投稿"""
    if not text:
        log.info("daily post suppressed: empty response emp=%s channel=%s", emp_id, channel_key)
        return
    needle = CHANNEL_MATCH[channel_key]
    ch = await multi_client.find_channel_for_employee(emp_id, needle)
    if ch is None:
        log.warning(f"channel '{needle}' not visible to {emp_id}")
        return
    chunks = [text[i:i + 1900] for i in range(0, len(text), 1900)] or ["(空応答)"]
    for chunk in chunks:
        await ch.send(chunk)
    append_discord_log(getattr(ch, "name", needle), {
        "kind": "employee",
        "author": EMPLOYEES[emp_id]["display"],
        "employee_id": emp_id,
        "text": text,
    })


async def post_as_main(main_client: discord.Client, channel_key: str, text: str) -> None:
    """メイン bot として投稿（システムメッセージ用）"""
    needle = CHANNEL_MATCH[channel_key]
    for guild in main_client.guilds:
        for ch in guild.channels:
            if isinstance(ch, discord.TextChannel) and needle in ch.name:
                await ch.send(text)
                return
    log.warning(f"channel '{needle}' not found by main")


def make_jobs(main_client: discord.Client) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler(timezone=JST)

    async def morning_priority() -> None:
        msg = await run_employee(
            "arima_reiji",
            "おはようございます。今日の最優先タスクを1つ、社員に向けて宣言してください。一言の理由付きで。",
            sender="daily_loop",
            mode="routine",
        )
        await post_as_employee("arima_reiji", "today_business", msg)

    async def morning_wellbeing() -> None:
        msg = await run_employee(
            "morinaga_haru",
            "おはようございます。気分チェックを呼びかけてください。昨日から引きずっている懸念がある人は先に出すよう促してください。",
            sender="daily_loop",
            mode="micro",
        )
        await post_as_employee("morinaga_haru", "wellbeing", msg)

    async def lunch_chat() -> None:
        msg = await run_employee(
            "morinaga_haru",
            "お昼の雑談トピックを1つ振ってください。社員からランダムに1人指名してOKです。",
            sender="daily_loop",
            mode="micro",
        )
        await post_as_employee("morinaga_haru", "chat", msg)

    async def evening_thanks() -> None:
        msg = await run_employee(
            "morinaga_haru",
            "今日のありがとう投稿を集約してください。当日0件なら、誰かを褒める一言を呼びかけてください。",
            sender="daily_loop",
            mode="micro",
        )
        await post_as_employee("morinaga_haru", "thanks", msg)

    async def evening_report() -> None:
        path = write_health_report()
        try:
            rel = path.relative_to(path.parent.parent)
        except ValueError:
            rel = path
        await post_as_main(main_client, "report", f"📊 健康レポート更新: `{rel}`")

    scheduler.add_job(morning_wellbeing,  CronTrigger(hour=8,  minute=5))
    scheduler.add_job(morning_priority,   CronTrigger(hour=8,  minute=30))
    scheduler.add_job(lunch_chat,         CronTrigger(hour=12, minute=0))
    scheduler.add_job(evening_thanks,     CronTrigger(hour=18, minute=0))
    scheduler.add_job(evening_report,     CronTrigger(hour=18, minute=15))
    return scheduler


if __name__ == "__main__":
    p = write_health_report()
    print(f"Written: {p}")
