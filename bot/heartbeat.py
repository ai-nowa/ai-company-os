"""会社の鼓動。30分ごとに沈黙チェック、90分以上沈黙していたら社員1人を軽く起動。

設計はシンプル:
- ロジックを社員側に任せる（時間帯・役割の if 分岐は持たない）
- 起こされた社員が自分の人格で「何を言うか」を判断する
- 応答に @ メンションが含まれていれば、いつもの連鎖機構で広がる

ブレーキ:
- 重み付きランダム（People/COO/CEOが起こされやすい）
- 23-7時はサイレント（usage節約）
"""
from __future__ import annotations

import asyncio
import json
import logging
import random
from datetime import datetime, timedelta
from typing import Optional

import discord
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from .config import BASE_DIR, EMPLOYEES, JST
from . import multi_client
from .employee_runner import run_employee_result

log = logging.getLogger("heartbeat")

CHECK_INTERVAL = 1800      # 30分ごとに沈黙チェック
IDLE_THRESHOLD = 5400      # 90分沈黙したら発火
DAILY_HEARTBEAT_LIMIT = 4
SILENT_HOUR_START = 23     # 23時〜
SILENT_HOUR_END = 7        # 7時 まではサイレント

# 起こされやすさの重み（人格的に「自発発言しやすい」役職を重め）
WEIGHTS: dict[str, int] = {
    "morinaga_haru": 4,    # People（空気作り、雑談振り）
    "saegusa_mio":   4,    # COO（タスク整理、進捗確認）
    "hinata_nagi":   1,    # 視聴者代表（軽い外部目線）
}


def get_last_activity_time() -> Optional[datetime]:
    """直近の Discord メッセージ時刻を取得"""
    discord_log_dir = BASE_DIR / "company" / "discord_log"
    if not discord_log_dir.exists():
        return None
    latest: Optional[datetime] = None
    for f in discord_log_dir.glob("*.jsonl"):
        try:
            for line in f.read_text(encoding="utf-8").splitlines():
                try:
                    e = json.loads(line)
                    ts = datetime.fromisoformat(e["ts"])
                    if ts.tzinfo is None:
                        ts = ts.replace(tzinfo=JST)
                    if latest is None or ts > latest:
                        latest = ts
                except (json.JSONDecodeError, ValueError, KeyError):
                    continue
        except Exception:
            continue
    return latest


def get_last_heartbeat_time() -> Optional[datetime]:
    """各社員の conversation_log で sender='heartbeat' の最新時刻を取得（連発防止）"""
    latest: Optional[datetime] = None
    for emp_id in EMPLOYEES.keys():
        log_file = BASE_DIR / "employees" / emp_id / "session" / "conversation_log.jsonl"
        if not log_file.exists():
            continue
        try:
            for line in log_file.read_text(encoding="utf-8").splitlines():
                try:
                    e = json.loads(line)
                    if e.get("kind") != "in" or e.get("from") != "heartbeat":
                        continue
                    ts = datetime.fromisoformat(e["ts"])
                    if ts.tzinfo is None:
                        ts = ts.replace(tzinfo=JST)
                    if latest is None or ts > latest:
                        latest = ts
                except (json.JSONDecodeError, ValueError, KeyError):
                    continue
        except Exception:
            continue
    return latest


def get_today_heartbeat_count() -> int:
    today = datetime.now(JST).date()
    count = 0
    for emp_id in EMPLOYEES.keys():
        log_file = BASE_DIR / "employees" / emp_id / "session" / "conversation_log.jsonl"
        if not log_file.exists():
            continue
        try:
            for line in log_file.read_text(encoding="utf-8").splitlines():
                try:
                    e = json.loads(line)
                    if e.get("kind") != "in" or e.get("from") != "heartbeat":
                        continue
                    ts = datetime.fromisoformat(e["ts"])
                    if ts.tzinfo is None:
                        ts = ts.replace(tzinfo=JST)
                    if ts.date() == today:
                        count += 1
                except (json.JSONDecodeError, ValueError, KeyError):
                    continue
        except Exception:
            continue
    return count


def pick_employee() -> str:
    employees = list(WEIGHTS.keys())
    weights = [WEIGHTS[e] for e in employees]
    return random.choices(employees, weights=weights, k=1)[0]


def is_silent_hour(now: datetime) -> bool:
    # 2026-05-23 いくと禁止令: AI に人間スケジュール持ち込み NG。深夜停止しない。
    # 例外（マーケ戦略上の待ち）は呼び出し側の戦略判断で対応。
    return False


async def heartbeat_tick(main_client: discord.Client) -> None:
    """1 tick: 沈黙チェック → 誰か起こす"""
    now = datetime.now(JST)
    if is_silent_hour(now):
        return

    last_activity = get_last_activity_time()
    if last_activity is None:
        return
    idle = (now - last_activity).total_seconds()
    if idle < IDLE_THRESHOLD:
        return
    if get_today_heartbeat_count() >= DAILY_HEARTBEAT_LIMIT:
        log.info("heartbeat: daily limit reached")
        return

    # 直前の heartbeat 発火から最低 IDLE_THRESHOLD 経っていることを確認（連発防止）
    last_hb = get_last_heartbeat_time()
    if last_hb is not None and (now - last_hb).total_seconds() < IDLE_THRESHOLD:
        return

    emp = pick_employee()
    log.info(f"heartbeat: {int(idle/60)}分沈黙、{emp} を自発発火")

    prompt = (
        f"会社で {int(idle/60)} 分ほど誰の発言もない状態です。"
        f"あなたの人格・役割として、Discordに短く自然な一言を投稿してください。"
        f"ただの活動演出ではなく、state_digestにある会社文脈から気になった違和感、"
        f"横断アイデア、軽い問い、または人間らしい雑談を1つだけ出してください。"
        f"新しい仮説や着想なら行頭に [IDEA] を付けてください。"
        f"300文字以内。緊急でない限り複数人を呼ばないでください。"
    )

    try:
        result = await run_employee_result(
            emp,
            prompt,
            sender="heartbeat",
            mode="micro",
            reason=f"heartbeat idle {int(idle/60)}min",
        )
    except Exception:
        log.exception(f"heartbeat run_employee failed: {emp}")
        return
    if not result.ok or not result.text:
        log.info("heartbeat response suppressed: emp=%s reason=%s", emp, result.skipped_reason)
        return
    msg = result.text

    # 投稿先: その社員の default_channels の最初（"all" の場合は給湯室）
    info = EMPLOYEES[emp]
    chans = info.get("default_channels", ["給湯室"])
    target_name = chans[0] if chans and chans[0] != "all" else "給湯室"
    ch = await multi_client.find_channel_for_employee(emp, target_name)
    if ch is None:
        ch = await multi_client.find_channel_for_employee(emp, "給湯室")
    if ch is None:
        log.warning(f"heartbeat: channel not found for {emp}")
        return

    # 投稿（テキスト→Discord メンション変換 + メタタグ除去）
    try:
        from .dispatcher import convert_text_mentions_to_discord
        from .mention_chain import strip_meta_tag
        clean = strip_meta_tag(msg)
        discord_text = convert_text_mentions_to_discord(clean)
    except Exception:
        discord_text = msg

    from .dispatcher import send_employee_response
    posted = await send_employee_response(emp, ch, discord_text)
    if not posted:
        return

    # 連鎖発火（メンションが含まれていれば次の社員が動く）
    try:
        from .dispatcher import process_mention_chain
        from .mention_chain import strip_meta_tag
        await process_mention_chain(
            f"{strip_meta_tag(msg)}\n{discord_text}",
            emp,
            ch,
            depth=0,
            visited={emp},
            origin="heartbeat",
        )
    except Exception:
        log.exception("heartbeat 連鎖発火失敗")


def make_heartbeat_scheduler(main_client: discord.Client) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler(timezone=JST)

    async def job() -> None:
        try:
            await heartbeat_tick(main_client)
        except Exception:
            log.exception("heartbeat tick error")

    scheduler.add_job(job, IntervalTrigger(seconds=CHECK_INTERVAL))
    return scheduler
