"""Discord bot メインループ。
- 受信メッセージを company/discord_log/{channel}.jsonl に追記
- メンション/コマンドで該当社員に転送し、応答を返す
- 起動時に日次スケジューラ(daily_loop)を開始
"""
from __future__ import annotations

import logging
import os
import re
from typing import Optional

import discord

from .config import (
    DISCORD_BOT_TOKEN,
    DISPLAY_TO_ID,
    EMPLOYEES,
    append_discord_log,
)
from .architect import run_architect
from .employee_runner import run_employee
from .triad_router import detect_decision_signal, describe_triad

logging.basicConfig(
    level=os.environ.get("LOG_LEVEL", "INFO"),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
log = logging.getLogger("dispatcher")

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

MENTION_DISPLAY_RE = re.compile("|".join(re.escape(d) for d in DISPLAY_TO_ID.keys()))
COMMAND_RE = re.compile(r"^!ask\s+(\w+)\s+(.+)$", re.DOTALL)
ARCHITECT_COMMAND_RE = re.compile(r"^!architect\s+(.+)$", re.DOTALL)
KICKOFF_COMMAND_RE = re.compile(r"^!kickoff(?:\s+(.*))?$", re.DOTALL)
USER_MENTION_RE = re.compile(r"<@!?\d+>")

# Discord ユーザー名 → 社内呼称
OWNER_DISCORD_NAMES = {"ikuto", "yikuto", "yikuto9805", "0ja3865p244394s"}


def normalize_sender(discord_name: str) -> str:
    """Discord ユーザー名から社内呼称を解決。創業者ならフラットな名前で社員に伝える"""
    base = discord_name.split("#")[0].lower()
    if base in OWNER_DISCORD_NAMES or "ikuto" in base:
        return "いくと"
    return discord_name


def resolve_target(content: str) -> Optional[str]:
    """本文から宛先社員IDを推定。表示名→英語IDの順で探す"""
    m = MENTION_DISPLAY_RE.search(content)
    if m:
        return DISPLAY_TO_ID[m.group(0)]
    for emp_id in EMPLOYEES.keys():
        if emp_id in content:
            return emp_id
    return None


@client.event
async def on_ready() -> None:
    log.info(f"Logged in as {client.user}")
    # 日次スケジューラ起動（dispatcher内で常駐）
    from .daily_loop import make_jobs
    scheduler = make_jobs(client)
    scheduler.start()
    log.info("Daily scheduler started (08:05/08:30/12:00/18:00/18:15)")


@client.event
async def on_message(message: discord.Message) -> None:
    if message.author == client.user:
        return

    channel_name = getattr(message.channel, "name", "dm")
    raw = message.content.strip()

    append_discord_log(channel_name, {
        "kind": "human" if not message.author.bot else "bot_other",
        "author": str(message.author),
        "text": raw,
    })

    # !kickoff コマンド: 創業者だけが発火できる、会社始動シーケンス
    kick_cmd = KICKOFF_COMMAND_RE.match(raw)
    if kick_cmd:
        if normalize_sender(str(message.author)) != "いくと":
            await message.channel.send("`!kickoff` は創業者のみ実行可能です。")
            return
        from .kickoff import kickoff as run_kickoff_sequence
        try:
            await message.channel.send("📡 AI NOWA キックオフを開始します...")
            await run_kickoff_sequence(client)
            await message.channel.send("✓ キックオフ完了。自律運営フェーズに移行しました。")
        except Exception as e:
            log.exception("kickoff failed")
            await message.channel.send(f"(キックオフ失敗: {type(e).__name__}: {e})")
        return

    # !architect コマンド: Co-Founder Claude（設計者）を呼ぶ
    arch_cmd = ARCHITECT_COMMAND_RE.match(raw)
    if arch_cmd:
        msg = arch_cmd.group(1)
        try:
            async with message.channel.typing():
                response = await run_architect(
                    msg,
                    sender=normalize_sender(str(message.author)),
                    channel=channel_name,
                )
        except Exception as e:
            log.exception("run_architect failed")
            response = f"(Architect 起動失敗: {type(e).__name__}: {e})"
        chunks = [response[i:i + 1900] for i in range(0, len(response), 1900)] or ["(空応答)"]
        for i, chunk in enumerate(chunks):
            await message.channel.send(("**Claude（設計者）**:\n" if i == 0 else "") + chunk)
        return

    # !ask コマンド優先
    cmd = COMMAND_RE.match(raw)
    if cmd:
        target = cmd.group(1)
        msg = cmd.group(2)
    else:
        target = resolve_target(raw)
        msg = raw
        if target is None:
            # 宛先不明: bot自身がメンションされていれば COO ミオが受ける
            if client.user in message.mentions:
                target = "saegusa_mio"
                msg = USER_MENTION_RE.sub("", raw).strip()
            else:
                return

    if target not in EMPLOYEES:
        await message.channel.send(f"未登録の社員です: `{target}`")
        return

    # トライアド検知
    triad_hint = detect_decision_signal(raw)
    prefix = f"[{describe_triad(triad_hint)}]\n" if triad_hint else ""

    try:
        async with message.channel.typing():
            response = await run_employee(
                target,
                prefix + msg,
                sender=normalize_sender(str(message.author)),
                channel=channel_name,
            )
    except Exception as e:
        log.exception("run_employee failed")
        response = f"(社員 {target} の起動に失敗: {type(e).__name__}: {e})"

    display = EMPLOYEES[target]["display"]
    # Discord 2000文字制限を簡易対応
    chunks = [response[i:i + 1900] for i in range(0, len(response), 1900)] or ["(空応答)"]
    header = f"**{display}**:\n"
    for i, chunk in enumerate(chunks):
        await message.channel.send((header if i == 0 else "") + chunk)


def main() -> None:
    if not DISCORD_BOT_TOKEN:
        raise RuntimeError("DISCORD_BOT_TOKEN が未設定です (.env を確認)")
    client.run(DISCORD_BOT_TOKEN)


if __name__ == "__main__":
    main()
