"""AutoMod 違反監視 → 24h 3回以上で自動 BAN。

discord.py の on_automod_action イベントを購読し、違反履歴を
company/.spam_violations.jsonl に追記。同一 user_id が 24h 以内に
3 回以上違反したら guild.ban() を実行し、#経営会議 に通知する。

9 社員 bot は user.bot=True で除外。
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path

import discord

REPO_ROOT = Path(__file__).parent.parent
VIOLATIONS_PATH = REPO_ROOT / "company" / ".spam_violations.jsonl"
JST = timezone(timedelta(hours=9))

BAN_WINDOW_HOURS = 24
BAN_THRESHOLD = 3
NOTIFY_CHANNEL_SUBSTR = "経営会議"

log = logging.getLogger("spam_auto_ban")


def _record_violation(execution: discord.AutoModAction, rule_name: str) -> None:
    """違反を JSONL に追記する。"""
    VIOLATIONS_PATH.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "ts": datetime.now(JST).isoformat(),
        "user_id": str(execution.user_id),
        "guild_id": str(execution.guild_id),
        "rule_name": rule_name,
        "rule_id": str(execution.rule_id),
        "channel_id": str(execution.channel_id) if execution.channel_id else "",
    }
    with VIOLATIONS_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def _count_recent_violations(user_id: str) -> int:
    """直近 BAN_WINDOW_HOURS 時間以内の違反数を返す。"""
    if not VIOLATIONS_PATH.exists():
        return 0
    cutoff = datetime.now(JST) - timedelta(hours=BAN_WINDOW_HOURS)
    count = 0
    for line in VIOLATIONS_PATH.read_text(encoding="utf-8").splitlines():
        try:
            entry = json.loads(line)
            if entry.get("user_id") != user_id:
                continue
            ts = datetime.fromisoformat(entry["ts"])
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=JST)
            if ts >= cutoff:
                count += 1
        except Exception:
            continue
    return count


async def _resolve_rule_name(guild: discord.Guild, rule_id: int) -> str:
    """rule_id から rule name を解決する。失敗時は trigger 種別 or id を返す。"""
    try:
        rule = await guild.fetch_automod_rule(rule_id)
        return rule.name or f"rule_{rule_id}"
    except Exception:
        return f"rule_{rule_id}"


async def _find_notify_channel(guild: discord.Guild) -> discord.TextChannel | None:
    """経営会議チャンネルを探す。"""
    for ch in guild.text_channels:
        if NOTIFY_CHANNEL_SUBSTR in ch.name:
            return ch
    return None


async def _notify_ban(
    guild: discord.Guild,
    user: discord.abc.User | discord.Member,
    violations: int,
    last_rule: str,
) -> None:
    """BAN 実行を経営会議に通知する。"""
    ch = await _find_notify_channel(guild)
    if ch is None:
        log.warning("通知チャンネル '%s' が見つかりません", NOTIFY_CHANNEL_SUBSTR)
        return
    msg = (
        f"🚨 **AutoMod 自動 BAN 実行**\n"
        f"対象: <@{user.id}> (`{user}`)\n"
        f"違反数: {violations} 回 / 直近 {BAN_WINDOW_HOURS}h\n"
        f"直近ルール: `{last_rule}`\n"
        f"理由: AutoMod {BAN_WINDOW_HOURS}h で {BAN_THRESHOLD} 回違反"
    )
    try:
        await ch.send(msg)
    except discord.HTTPException as e:
        log.warning("通知投稿失敗: %s", e)


async def handle_automod_action(
    client: discord.Client,
    execution: discord.AutoModAction,
) -> None:
    """AutoMod 違反 1 件を処理する。記録 → 閾値チェック → BAN。"""
    guild = client.get_guild(execution.guild_id)
    if guild is None:
        log.warning("guild not found: %s", execution.guild_id)
        return

    # 9 社員 bot 除外: member 取得して bot 判定
    member = guild.get_member(execution.user_id)
    if member is not None and member.bot:
        log.debug("bot 違反のためスキップ: %s", member)
        return

    rule_name = await _resolve_rule_name(guild, execution.rule_id)
    _record_violation(execution, rule_name)
    log.info(
        "AutoMod 違反記録: user=%s rule=%s channel=%s",
        execution.user_id, rule_name, execution.channel_id,
    )

    user_id_str = str(execution.user_id)
    violations = _count_recent_violations(user_id_str)
    if violations < BAN_THRESHOLD:
        return

    # BAN 実行
    user_obj: discord.abc.User | discord.Member | None = member
    if user_obj is None:
        try:
            user_obj = await client.fetch_user(execution.user_id)
        except Exception as e:
            log.warning("user fetch 失敗: %s (%s)", execution.user_id, e)
            return

    try:
        await guild.ban(
            user_obj,
            reason=f"AutoMod {BAN_WINDOW_HOURS}h {violations} violations",
            delete_message_days=1,
        )
        log.warning("自動 BAN 実行: user=%s violations=%d", user_obj, violations)
        await _notify_ban(guild, user_obj, violations, rule_name)
    except discord.Forbidden:
        log.error("BAN 失敗（権限不足）: user=%s", user_obj)
    except discord.HTTPException as e:
        log.error("BAN 失敗: user=%s err=%s", user_obj, e)


def setup(client: discord.Client) -> None:
    """main_client に on_automod_action リスナーを登録する。"""
    @client.event
    async def on_automod_action(execution: discord.AutoModAction) -> None:
        try:
            await handle_automod_action(client, execution)
        except Exception:
            log.exception("on_automod_action 処理失敗")

    log.info("spam_auto_ban setup 完了 (threshold=%d/%dh)", BAN_THRESHOLD, BAN_WINDOW_HOURS)
