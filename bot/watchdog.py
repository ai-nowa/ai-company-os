"""dispatcher 監視 + 自動修復 + Architect 相談 + ユーザー通知 (Phase 2.8)。

4層の自動回復:
  Layer 1: dispatcher プロセス停止 → 30秒以内に即再起動
  Layer 2: 1時間で 5回以上再起動 → 設計者（Opus）に自動相談
  Layer 3: Architect 判断が ESCALATE → Discord で @yikuto9805 通知
  Layer 4: セッション開始時の自動報告 (CLAUDE.md 経由、別途仕組み)

起動方法:
  nohup bot/.venv/bin/python -m bot.watchdog > /tmp/ai_nowa_watchdog.log 2>&1 &

停止方法:
  python3 -c "import os,signal,subprocess; r=subprocess.run(['ps','-eo','pid,args','--no-headers'],capture_output=True,text=True); [os.kill(int(l.split()[0]),signal.SIGTERM) for l in r.stdout.splitlines() if '-m bot.watchdog' in l and (l.split()[1].endswith('python') or l.split()[1].endswith('python3'))]"
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import discord

from .architect import run_architect
from .config import BASE_DIR, DISCORD_BOT_TOKEN, JST, now_jst_iso
from . import dispatcher_manager

logging.basicConfig(
    level=os.environ.get("LOG_LEVEL", "INFO"),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
log = logging.getLogger("watchdog")

INCIDENTS_FILE = BASE_DIR / "company" / "incidents.jsonl"
WATCHDOG_STATE_FILE = BASE_DIR / "company" / "watchdog_state.json"
HEALTHCHECK_INTERVAL = 30
MAX_AUTO_RESTARTS_PER_HOUR = 5
OWNER_DISCORD_HANDLE = "yikuto9805"
NOTIFY_CHANNEL_NEEDLES = ["インシデント", "監査部", "お知らせ"]  # 上から順に試す


def log_incident(
    kind: str,
    detail: str,
    severity: str = "info",
    status: str = "open",
    extra: Optional[dict] = None,
) -> dict:
    """インシデントを company/incidents.jsonl に追記。severity: info/warning/error/critical"""
    INCIDENTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "ts": now_jst_iso(),
        "kind": kind,
        "severity": severity,
        "status": status,
        "detail": detail,
    }
    if extra:
        entry.update(extra)
    with INCIDENTS_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    log.info(f"[incident:{severity}] {kind}: {detail[:120]}")
    return entry


def mark_resolved(kind: str, action_taken: str) -> None:
    """直近の同種オープンインシデントを resolved に更新（簡易版: 追記で記録）"""
    log_incident(
        kind=f"{kind}_resolved",
        detail=f"Resolved by: {action_taken}",
        severity="info",
        status="resolved",
        extra={"action_taken": action_taken},
    )


def recent_restart_count(within_minutes: int = 60) -> int:
    if not INCIDENTS_FILE.exists():
        return 0
    cutoff = datetime.now(JST) - timedelta(minutes=within_minutes)
    count = 0
    for line in INCIDENTS_FILE.read_text(encoding="utf-8").splitlines():
        try:
            e = json.loads(line)
            if e.get("kind") == "auto_restart":
                ts = datetime.fromisoformat(e["ts"])
                if ts.tzinfo is None:
                    ts = ts.replace(tzinfo=JST)
                if ts >= cutoff:
                    count += 1
        except (json.JSONDecodeError, ValueError, KeyError):
            continue
    return count


def employee_error_count(within_minutes: int = 30) -> dict[str, int]:
    """各社員の最近のエラー応答カウント（"(エラー:" を含む out メッセージ）"""
    counts: dict[str, int] = {}
    cutoff = datetime.now(JST) - timedelta(minutes=within_minutes)
    employees_dir = BASE_DIR / "employees"
    for emp_dir in employees_dir.iterdir():
        if not emp_dir.is_dir():
            continue
        log_file = emp_dir / "session" / "conversation_log.jsonl"
        if not log_file.exists():
            continue
        n = 0
        try:
            for line in log_file.read_text(encoding="utf-8").splitlines():
                try:
                    e = json.loads(line)
                    if e.get("kind") != "out":
                        continue
                    text = e.get("text", "")
                    if "(エラー:" not in text:
                        continue
                    ts = datetime.fromisoformat(e["ts"])
                    if ts.tzinfo is None:
                        ts = ts.replace(tzinfo=JST)
                    if ts >= cutoff:
                        n += 1
                except (json.JSONDecodeError, ValueError, KeyError):
                    continue
        except Exception:
            continue
        if n > 0:
            counts[emp_dir.name] = n
    return counts


async def consult_architect(situation: str) -> str:
    """Architect Claude にインシデント対処を相談（自動回復方針取得）"""
    msg = (
        f"監視 (watchdog) からの自動通知です。\n\n"
        f"=== 状況 ===\n{situation}\n\n"
        f"次の3つから選んで簡潔に判断してください:\n"
        f"1. 再起動を続行 → そのまま再試行\n"
        f"2. 原因調査が必要 → どこを見るべきか具体的に指示\n"
        f"3. いくとに通知 → なぜ判断不能か理由を一言\n\n"
        f"先頭に **[ACTION: RESTART|INVESTIGATE|ESCALATE]** のタグを必ず付けてください。"
    )
    try:
        return await run_architect(msg, sender="watchdog", mode="incident", use_resume=False)
    except Exception as e:
        log.exception("Architect 相談失敗")
        return "[ACTION: ESCALATE] Architect 相談が一時的に失敗。詳細はサーバーログを確認。"


def parse_action(advice: str) -> str:
    """Architect 応答から ACTION タグを抽出（RESTART/INVESTIGATE/ESCALATE）"""
    m = re.search(r"\[ACTION:\s*(\w+)\s*\]", advice, re.IGNORECASE)
    if m:
        action = m.group(1).upper()
        if action in ("RESTART", "INVESTIGATE", "ESCALATE"):
            return action
    return "RESTART"  # デフォルト


async def notify_owner_via_discord(summary: str, severity: str = "warning") -> None:
    """Discord で @yikuto9805 に通知。NOTIFY_CHANNEL_NEEDLES の順で投稿先を探す"""
    if not DISCORD_BOT_TOKEN:
        log.error("DISCORD_BOT_TOKEN 未設定")
        return
    intents = discord.Intents.default()
    intents.message_content = True
    client = discord.Client(intents=intents)
    severity_emoji = {"info": "ℹ️", "warning": "⚠️", "error": "🚨", "critical": "🔥"}
    emoji = severity_emoji.get(severity, "⚠️")

    posted = False

    @client.event
    async def on_ready() -> None:
        nonlocal posted
        try:
            for guild in client.guilds:
                target_ch = None
                for needle in NOTIFY_CHANNEL_NEEDLES:
                    for ch in guild.channels:
                        if isinstance(ch, discord.TextChannel) and needle in ch.name:
                            target_ch = ch
                            break
                    if target_ch:
                        break
                if target_ch is None:
                    continue
                body = (
                    f"{emoji} **Watchdog Alert** [{severity.upper()}]\n"
                    f"@{OWNER_DISCORD_HANDLE} 自動修復で対処できない状況です:\n\n"
                    f"```\n{summary[:1500]}\n```\n"
                    f"詳細は `company/incidents.jsonl` に記録されています。"
                )
                await target_ch.send(body)
                posted = True
                return
        finally:
            await client.close()

    try:
        await client.start(DISCORD_BOT_TOKEN)
    except Exception:
        log.exception("Discord 通知失敗")
    if not posted:
        log.warning("どの通知チャンネルにも投稿できませんでした")


async def handle_dispatcher_down() -> None:
    log.warning("dispatcher 停止検知")
    log_incident(
        "dispatcher_down",
        "dispatcher process not found",
        severity="error",
    )
    recent = recent_restart_count(60)

    # Layer 2: Architect 相談 (5回以上再起動済み)
    if recent >= MAX_AUTO_RESTARTS_PER_HOUR:
        log.warning(f"直近1時間で {recent} 回再起動。Architect に相談")
        log_incident(
            "escalate_to_architect",
            f"直近1時間で {recent} 回再起動済み、設計者に判断仰ぐ",
            severity="warning",
        )
        advice = await consult_architect(
            f"dispatcher が再び停止しました。"
            f"直近1時間で既に {recent} 回 (上限 {MAX_AUTO_RESTARTS_PER_HOUR}) 再起動しています。"
            f"通常を超えた頻度です。設計や認証など根本問題の可能性。"
        )
        log_incident("architect_advice", advice[:600], severity="info",
                     extra={"action": parse_action(advice)})

        action = parse_action(advice)
        if action == "ESCALATE":
            # Layer 3: ユーザー通知
            await notify_owner_via_discord(
                f"dispatcher が連続失敗 (1h で {recent} 回再起動)。\n"
                f"Architect 判断: ESCALATE\n\n{advice[:800]}",
                severity="critical",
            )
            log_incident("escalated_to_owner", "Discord 通知済", severity="critical")
            return
        if action == "INVESTIGATE":
            log_incident("investigation_pending", advice[:500], severity="warning")
            return
        # RESTART は下に進む

    # Layer 1: 自動再起動
    log.info("dispatcher を自動再起動")
    pid = dispatcher_manager.start_dispatcher()
    if pid:
        log_incident("auto_restart", f"new pid={pid}", severity="info",
                     status="resolved", extra={"new_pid": pid})
        log.info(f"再起動完了 (pid={pid})")
    else:
        log_incident("auto_restart_failed", "start_dispatcher が PID を返さない",
                     severity="critical")
        await notify_owner_via_discord(
            "自動再起動が失敗しました。手動介入が必要です。",
            severity="critical",
        )


def check_employee_health() -> Optional[dict[str, int]]:
    """各社員のエラー発生率をチェック。3エラー/30分以上の社員リストを返す"""
    counts = employee_error_count(within_minutes=30)
    problem = {emp: n for emp, n in counts.items() if n >= 3}
    return problem if problem else None


async def watchdog_loop() -> None:
    log.info(f"Watchdog 起動 (interval={HEALTHCHECK_INTERVAL}s, max_restart/h={MAX_AUTO_RESTARTS_PER_HOUR})")
    log_incident("watchdog_started", f"interval={HEALTHCHECK_INTERVAL}s", severity="info")

    last_employee_check = datetime.now(JST)

    while True:
        try:
            # dispatcher 生死チェック
            if not dispatcher_manager.is_dispatcher_running():
                await handle_dispatcher_down()

            # 社員エラー率チェック (10分に1回)
            if (datetime.now(JST) - last_employee_check).seconds > 600:
                problem = check_employee_health()
                if problem:
                    detail = ", ".join(f"{e}={n}" for e, n in problem.items())
                    log_incident(
                        "employee_error_spike",
                        f"30分以内に3回以上エラー応答: {detail}",
                        severity="warning",
                    )
                last_employee_check = datetime.now(JST)

            await asyncio.sleep(HEALTHCHECK_INTERVAL)
        except KeyboardInterrupt:
            log.info("Watchdog 終了 (KeyboardInterrupt)")
            log_incident("watchdog_stopped", "KeyboardInterrupt", severity="info")
            break
        except Exception as e:
            log.exception("watchdog loop error")
            log_incident("watchdog_error", f"{type(e).__name__}: {e}",
                         severity="error")
            await asyncio.sleep(HEALTHCHECK_INTERVAL)


if __name__ == "__main__":
    asyncio.run(watchdog_loop())
