"""日次スケジューラ。
APScheduler で朝/昼/夕の自動投稿と健康レポート更新を発火する。
dispatcher.py の on_ready から make_jobs(client).start() で起動する想定。
"""
from __future__ import annotations

import logging
from typing import Optional

import discord
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from .config import JST
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


async def post_to_channel(client: discord.Client, key: str, content: str) -> None:
    needle = CHANNEL_MATCH[key]
    for guild in client.guilds:
        for ch in guild.channels:
            if isinstance(ch, discord.TextChannel) and needle in ch.name:
                await ch.send(content)
                return
    log.warning(f"チャンネルが見つからない: {needle}")


def make_jobs(client: discord.Client) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler(timezone=JST)

    async def morning_priority() -> None:
        msg = await run_employee(
            "arima_reiji",
            "おはようございます。今日の最優先タスクを1つ、社員に向けて宣言してください。一言の理由付き。",
            sender="daily_loop",
        )
        await post_to_channel(client, "today_business", f"**有馬レイジ**:\n{msg}")

    async def morning_wellbeing() -> None:
        msg = await run_employee(
            "morinaga_haru",
            "おはようございます。気分チェックを呼びかけてください。昨日から引きずっている懸念がある人は先に出すよう促してください。",
            sender="daily_loop",
        )
        await post_to_channel(client, "wellbeing", f"**森永ハル**:\n{msg}")

    async def lunch_chat() -> None:
        msg = await run_employee(
            "morinaga_haru",
            "お昼の雑談トピックを1つ振ってください。社員からランダムに1人指名してOKです。",
            sender="daily_loop",
        )
        await post_to_channel(client, "chat", f"**森永ハル**:\n{msg}")

    async def evening_thanks() -> None:
        msg = await run_employee(
            "morinaga_haru",
            "今日のありがとう投稿を集約してください。当日0件なら、誰かを褒める一言を呼びかけてください。",
            sender="daily_loop",
        )
        await post_to_channel(client, "thanks", f"**森永ハル**:\n{msg}")

    async def evening_report() -> None:
        path = write_health_report()
        try:
            rel = path.relative_to(path.parent.parent)
        except ValueError:
            rel = path
        await post_to_channel(client, "report", f"📊 健康レポート更新: `{rel}`")

    scheduler.add_job(morning_wellbeing,  CronTrigger(hour=8,  minute=5))
    scheduler.add_job(morning_priority,   CronTrigger(hour=8,  minute=30))
    scheduler.add_job(lunch_chat,         CronTrigger(hour=12, minute=0))
    scheduler.add_job(evening_thanks,     CronTrigger(hour=18, minute=0))
    scheduler.add_job(evening_report,     CronTrigger(hour=18, minute=15))
    return scheduler


if __name__ == "__main__":
    # 単発デバッグ: ヘルスレポートだけ生成
    p = write_health_report()
    print(f"Written: {p}")
