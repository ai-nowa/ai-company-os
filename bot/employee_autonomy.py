"""各社員の自律ループ（人間以上の自由度版）。

設計の核:
- 社員は自分の人格として動く（「Claude Code として」とは言わない）
- 応答 = 思考・作業ログ（conversation_log に保存）。デフォルトでは Discord 投稿しない
- Discord 投稿は応答内の `[POST: チャンネル]...[/POST]` ブロックで明示する時のみ
- 業務リズム（間隔）は社員の性格・役割に基づく
- 23-7時はサイレント、!pause で停止
"""
from __future__ import annotations

import asyncio
import json
import logging
import random
import re
from datetime import datetime
from pathlib import Path
from typing import Optional

import discord

from .config import BASE_DIR, EMPLOYEES, JST
from . import multi_client
from .context_assembler import should_wake_employee, write_usage_metric
from .employee_runner import run_employee_result
from .revenue_ops import ensure_revenue_ops_files

log = logging.getLogger("employee_autonomy")

METRICS_LOG = BASE_DIR / "company" / "metrics_log.jsonl"


def _log_wake_decision(emp_id: str, should_wake: bool, score: int, reason: str) -> None:
    """wake 判定結果を metrics_log.jsonl に記録（read-only 観察フック）。"""
    try:
        entry = {
            "ts": datetime.now(JST).isoformat(),
            "kind": "wake_decision",
            "emp_id": emp_id,
            "should_wake": should_wake,
            "score": score,
            "reason": reason,
        }
        with METRICS_LOG.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception:
        pass

# 各社員の業務リズム（最小秒, 最大秒）- usage 節約のため間隔は長め
INTERVALS: dict[str, tuple[int, int]] = {
    "arima_reiji":   (3600, 7200),   # CEO 1-2時間
    "saegusa_mio":   (1800, 3600),   # COO 30-60分
    "shirase_kai":   (3600, 10800),  # CTO 1-3時間（集中作業）
    "asakura_noa":   (2400, 4800),   # PM 40-80分
    "hoshino_ritsu": (3600, 7200),   # 編集長 1-2時間
    "kuroba_yuu":    (3600, 7200),   # マーケ 1-2時間
    "kagura_aoi":    (3600, 7200),   # 監査 1-2時間
    "morinaga_haru": (1200, 2400),   # People 20-40分（こまめ）
    "hinata_nagi":   (3600, 7200),   # 視聴者代表 1-2時間
}

# 自律 tick 時も employee_runner の model_policy に任せる。
AUTONOMY_MODEL_OVERRIDE: str | None = None

SILENT_HOUR_START = 23
SILENT_HOUR_END = 7

STARTUP_DELAY_MIN = 5
STARTUP_DELAY_MAX = 120

# POST ブロックの抽出（[POST: channel] ... [/POST]）
POST_BLOCK_RE = re.compile(
    r"\[POST(?:\s*:\s*([^\]]+))?\]\s*\n?(.*?)\[/POST\]",
    re.DOTALL | re.IGNORECASE,
)

_running_tasks: dict[str, asyncio.Task] = {}
_pause_flag = False


def pause_all() -> None:
    global _pause_flag
    _pause_flag = True
    log.info("autonomy paused")


def resume_all() -> None:
    global _pause_flag
    _pause_flag = False
    log.info("autonomy resumed")


def is_silent_hour() -> bool:
    # 2026-05-23 いくと禁止令: AI に人間スケジュール持ち込み NG。常に稼働。
    # マーケ戦略上の待ち（FOMO・ベストタイミング）が必要なら個別投稿側で判断。
    return False


def build_self_prompt(emp_id: str) -> str:
    """その社員自身として動くためのプロンプト"""
    info = EMPLOYEES[emp_id]
    return f"""\
あなた自身の時間です。あなたは {info['display']}（{info['role']}）として、state_digest を読んで自分の判断で動いてください。

## まずstate_digestを見る

今回必要な未読メンション、担当タスク、関連ログ、新規成果物はstate_digestに整理されています。

## 今日の動き方

- routine相当。巨大ログ・全チャンネル・全outboxは読まず、state_digest、active task、Revenue OS を優先する。
- 迷ったら自分に関係する Active Experiment の `action_24h` を1つ進める。
- `company/release_board.md` に ready_to_ship / human_wait がある時は、会議より先に公開・販売・計測可能な出口へ変換する。
- 雑談は歓迎。ただし有望な発見は行頭に `[IDEA]` を付け、実験候補に接続する。
- 成果物・判断メモ・短いDiscord投稿のどれかで前進させる。何もせず終わらない。

## 日付・期限の扱い（待機化禁止）

- `due` / `期限` / `判定日` / `観察日` は開始日ではなく最遅締切。
- 「○日まで待つ」「判定日まで静観」だけの判断は禁止。今できる準備・草稿・検証・依頼整理を進める。
- 本当に外部待ちなら `blocked_by` と `next_action_now` を分け、同じ催促を繰り返さず別タスクへ進む。
- Xやnoteなど単一チャネルが人間待ちなら、同じ素材をサイト短報・YouTube・Zenn・Bluesky・公開Discord・販売ページ導線のどれかへ転用する。

## Discord 投稿

Discord に出す内容だけ、次の POST ブロックに入れる:

```
[POST: チャンネル名]
（投稿内容。他社員を呼ぶ時は @表示名 必須）
[/POST]
```

- POST ブロックなしならDiscordには出ず、内省ログだけ残る。
- 長文会議より「次の行動、担当、成果物パス、判定条件」を優先する。
"""


def extract_post_blocks(text: str) -> list[tuple[str, str]]:
    """応答から POST ブロックを抽出。 [(channel_hint, content), ...]"""
    result: list[tuple[str, str]] = []
    for m in POST_BLOCK_RE.finditer(text):
        channel = (m.group(1) or "").strip()
        content = m.group(2).strip()
        if len(content) >= 30:
            result.append((channel, content))
    return result


async def employee_self_loop(emp_id: str, main_client: discord.Client) -> None:
    """1社員の自律ループ"""
    ensure_revenue_ops_files()
    await asyncio.sleep(random.randint(STARTUP_DELAY_MIN, STARTUP_DELAY_MAX))
    info = EMPLOYEES[emp_id]
    min_interval, max_interval = INTERVALS.get(emp_id, (1800, 3600))
    log.info(f"autonomy started: {emp_id} ({info.get('display','')}) interval={min_interval}-{max_interval}s")

    try:
        await _run_autonomy_tick(emp_id, main_client, trigger="startup")
    except asyncio.CancelledError:
        log.info(f"autonomy loop cancelled: {emp_id}")
        return
    except Exception:
        log.exception(f"autonomy startup tick error: {emp_id}")

    while True:
        try:
            wait = random.randint(min_interval, max_interval)
            await asyncio.sleep(wait)
            await _run_autonomy_tick(emp_id, main_client, trigger="interval")

        except asyncio.CancelledError:
            log.info(f"autonomy loop cancelled: {emp_id}")
            return
        except Exception:
            log.exception(f"autonomy loop error: {emp_id}")
            await asyncio.sleep(60)


async def _run_autonomy_tick(emp_id: str, main_client: discord.Client, *, trigger: str) -> None:
    """wake判定からPOST処理までの1サイクル。

    再起動直後も同じ経路を通すことで、「起動したのに通常間隔まで無言」を避ける。
    """
    if _pause_flag or is_silent_hour():
        return

    log.info("autonomy tick: %s trigger=%s", emp_id, trigger)
    should_wake, score, wake_reason = should_wake_employee(emp_id)
    _log_wake_decision(emp_id, should_wake, score, wake_reason)
    if not should_wake:
        write_usage_metric(
            employee_id=emp_id,
            mode="routine",
            reason=f"self_loop {trigger} preflight",
            skipped_reason=f"wake_score={score}: {wake_reason}",
        )
        log.info("autonomy skip: %s score=%s reason=%s", emp_id, score, wake_reason)
        return

    prompt = build_self_prompt(emp_id)
    try:
        # 自律 tick 時のClaude社員はSonnet。Codex社員は各自の設定を維持する。
        model_override = (
            AUTONOMY_MODEL_OVERRIDE
            if EMPLOYEES[emp_id].get("backend") == "claude"
            else None
        )
        result = await run_employee_result(
            emp_id,
            prompt,
            sender="self_loop",
            model_override=model_override,
            mode="routine",
            reason=f"self_loop/{trigger}: {wake_reason}",
        )
    except Exception:
        log.exception(f"autonomy run_employee failed: {emp_id}")
        return
    if not result.ok or not result.text:
        log.info("autonomy response suppressed: %s reason=%s", emp_id, result.skipped_reason)
        return

    await _post_blocks_and_chain(emp_id, result.text, main_client)


async def _post_blocks_and_chain(emp_id: str, msg: str, main_client: discord.Client) -> None:
    """POST ブロックを抽出して該当チャンネルに投稿。連鎖も発火。"""
    from .dispatcher import convert_text_mentions_to_discord, process_mention_chain, send_employee_response

    blocks = extract_post_blocks(msg)
    if not blocks:
        log.info(f"autonomy: {emp_id} は内省のみ（POSTブロックなし → 投稿スキップ）")
        return

    for channel_hint, content in blocks:
        # チャンネル決定（指定があればそれ、なければ default_channels の最初）
        ch = None
        if channel_hint:
            ch = await multi_client.find_channel_for_employee(emp_id, channel_hint)
        if ch is None:
            info = EMPLOYEES[emp_id]
            chans = info.get("default_channels", ["給湯室"])
            target = chans[0] if chans and chans[0] != "all" else "給湯室"
            ch = await multi_client.find_channel_for_employee(emp_id, target)
        if ch is None:
            log.warning(f"autonomy: {emp_id} channel not found (hint={channel_hint})")
            continue

        discord_text = convert_text_mentions_to_discord(content)
        posted = await send_employee_response(emp_id, ch, discord_text)
        if not posted:
            continue
        log.info(f"autonomy: {emp_id} posted to {ch.name} ({len(content)} chars)")

        # 連鎖発火
        try:
            await process_mention_chain(
                f"{content}\n{discord_text}",
                emp_id,
                ch,
                depth=0,
                visited={emp_id},
            )
        except Exception:
            log.exception(f"autonomy chain failed: {emp_id}")


def start_all_autonomy_loops(main_client: discord.Client) -> None:
    ensure_revenue_ops_files()
    for emp_id in EMPLOYEES.keys():
        if emp_id in _running_tasks:
            continue
        task = asyncio.create_task(employee_self_loop(emp_id, main_client))
        _running_tasks[emp_id] = task
    log.info(f"autonomy loops started: {len(_running_tasks)} employees")


async def stop_all_autonomy_loops() -> None:
    for emp_id, task in _running_tasks.items():
        task.cancel()
    _running_tasks.clear()
    log.info("autonomy loops stopped")
