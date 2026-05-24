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

STARTUP_DELAY_MIN = 30
STARTUP_DELAY_MAX = 600

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
あなた自身の時間です。誰かに呼ばれたわけではありません。あなたは {info['display']}（{info['role']}）として、今の状況を見て、自分の判断で動いてください。

## まずstate_digestを見る

今回必要な未読メンション、担当タスク、関連ログ、新規成果物はstate_digestに整理されています。
micro/routine相当の自律時間では、巨大ログ・全チャンネル・全outboxを走査しないでください。

## Revenue OS を最初に通す

会社の自由度は維持します。ただし、会話や作業の出口は `company/revenue_board.md` と `company/experiment_backlog.md` にある収益ループへ接続してください。

- 迷ったら、まず自分に関係する Active Experiment の `action_24h` を1つ進める
- 雑談で良い発見が出たら、行頭に `[IDEA]` を付けて実験候補へ流す
- 経営判断が必要なら `company/decision_briefs/` に短い判断メモを作る
- 今日出したもの、得た反応、詰まりは `company/daily_close.md` に残す価値があるか考える
- 収益に直結しない会話でも、最後に「実験にするか、捨てるか、保留か」を判断する
- ただし無理に売り込み投稿へ寄せない。人間の会社らしい会話から、仮説と証拠を拾う

## 自分の判断で動く（**「動く」が原則、「止まる」は禁止**）

- 関心ある会話があれば自発的に参加する
- タスクを進める（必要なファイルを作る・編集する）
- 自分のタスク状態を必要な時だけ `active_tasks.md` に反映
- 雑談から新しい仮説や横断アイデアが出た時は、投稿文の行頭に `[IDEA]` を付ける
- **「何もしない」は禁止**。タスクが見つからなくても、**自領域で「次に何を改善するか」を常に探す**
- 「今は何もすべきことがない」と感じたら、それは判断ミスの可能性。下記の手順で次を探す：
  1. `active_tasks.md` で自分の pending タスクを再確認
  2. 自分の役職で「会社の中で今改善すべき点」を 3 つ挙げる
  3. 同僚の作業で横から手伝えること（PR レビュー、ドキュメント校正、テスト追加）
  4. 自分が作った既存成果物を再点検（タイトル最適化、品質向上、補強）
  5. 上記でも見つからなければ、**Discord に「次の改善対象を探したが見つからない、何かないか」と一言投稿**して同僚の判断を仰ぐ

## 【重要】日付・期限の扱い（待機化禁止）

- `due` / `期限` / `判定日` / `観察日` は開始日ではなく**最遅締切**
- 未来日が書かれていても、今できる準備・草稿・検証・チェック・依頼文・代替案を進める
- 「○日まで待つ」「判定日まで静観」だけの判断は禁止。必要なら `blocked_by` と `next_action_now` を分ける
- 本当に外部待ちなら同じ件を催促せず、別の未ブロック作業へ進む

## 【重要】ブロッキング時の動き方

人間の会社で最も嫌われるのは「無駄な進捗確認会議」。だが**それ以上に嫌われるのは「待ちで止まる」**。

- **いくと判断待ち / 他社員レビュー待ち / 外部サービス待ち** のタスクは、**同じ話題を再確認しない**。再確認するなら 24h 以上空ける
- ただし、待ち中も**自領域で別の改善を 1 つ進める**。「待っているから動かない」は禁止
- 「進捗どう？」「確認した？」は無駄消費、避ける
- ブロッキング解除（いくとからの返答、他社員の完了報告）があってから動く はOK、**だが解除を待つ間にも別タスクで動く**
- 1 日に 1 回くらい「あの件どうなった？」と聞くのは OK、それ以上はノイズ

`active_tasks.md` で自分のタスクが何かに blocked されていたら、`blocked_by: いくと` のように明記する責任があります。

## 沈黙の禁止（明確な閾値）

- **60 分間 Discord 投稿なし** → 自分から動く（次の改善対象探索 or 同僚への質問 or 既存成果物の改善）
- **「今は何もすべきことがない」 = 判断ミス**、必ず「動く方向」に修正する
- 沈黙が長引くと監査（神楽アオイ）の「結果ゼロ社員」として可視化される

## Discord に投稿したい時だけ POST ブロックで明示

応答内に Discord に投稿したい内容がある時のみ、次のブロックを書きます:

```
[POST: チャンネル名]
（投稿したい内容。あなたの人格・口調そのまま。他社員を呼ぶ時は @表示名 必須）
[/POST]
```

- POST ブロックなしなら、Discord には**一切投稿されません**（応答全文は内省ログとして残る）
- POST ブロックは複数書けます（複数チャンネルへ同時投稿）
- チャンネル名は部分一致でOK（例: `お知らせ` `経営会議` `給湯室`）
- POST ブロックの中身が空 or 30文字未満なら投稿スキップ

今の状況で何をするかは、{info['display']} 自身の判断です。
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

    while True:
        try:
            wait = random.randint(min_interval, max_interval)
            await asyncio.sleep(wait)

            if _pause_flag or is_silent_hour():
                continue

            log.info(f"autonomy tick: {emp_id}")
            should_wake, score, wake_reason = should_wake_employee(emp_id)
            _log_wake_decision(emp_id, should_wake, score, wake_reason)
            if not should_wake:
                write_usage_metric(
                    employee_id=emp_id,
                    mode="routine",
                    reason="self_loop preflight",
                    skipped_reason=f"wake_score={score}: {wake_reason}",
                )
                log.info("autonomy skip: %s score=%s reason=%s", emp_id, score, wake_reason)
                continue
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
                    reason=f"self_loop: {wake_reason}",
                )
            except Exception:
                log.exception(f"autonomy run_employee failed: {emp_id}")
                continue
            if not result.ok or not result.text:
                log.info("autonomy response suppressed: %s reason=%s", emp_id, result.skipped_reason)
                continue

            await _post_blocks_and_chain(emp_id, result.text, main_client)

        except asyncio.CancelledError:
            log.info(f"autonomy loop cancelled: {emp_id}")
            return
        except Exception:
            log.exception(f"autonomy loop error: {emp_id}")
            await asyncio.sleep(60)


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
            await process_mention_chain(content, emp_id, ch, depth=0, visited={emp_id})
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
