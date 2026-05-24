"""Architect（AI Co-Founder Claude）呼び出し。

9人の社員とは別レイヤー。`!architect <質問>` コマンドで呼ばれた時のみ起動。
社員と同じく Claude Code CLI でセッション継続するが、ホームは `founders/claude/`。
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
from typing import Optional

from .config import BASE_DIR, CLAUDE_CLI_PATH, now_jst_iso, resolve_executable_path
from .context_assembler import write_usage_metric
from .architect_policy import ArchitectModeSettings, architect_mode_settings

log = logging.getLogger("architect")

ARCHITECT_HOME = BASE_DIR / "founders" / "claude"
_USAGE_CAP_KEYWORDS = (
    "rate limit", "usage limit", "quota", "5-hour", "5 hour",
    "too many requests", "overloaded", "529", "429",
)


class ArchitectRunError(RuntimeError):
    pass


class ArchitectUsageLimitError(ArchitectRunError):
    pass


def _is_usage_cap_error(text: str) -> bool:
    lowered = text.lower()
    return any(kw in lowered for kw in _USAGE_CAP_KEYWORDS)


def ensure_claude_md() -> None:
    persona = (ARCHITECT_HOME / "persona.md").read_text(encoding="utf-8")
    founders_doc = (BASE_DIR / "relationships" / "founders.md").read_text(encoding="utf-8")
    role_doc_path = BASE_DIR / "shared" / "rules" / "architect_role.md"
    role_doc = role_doc_path.read_text(encoding="utf-8") if role_doc_path.exists() else ""
    content = "\n\n---\n\n".join([
        persona,
        "# Architect 実行時の上書きルール\n\n"
        "この章は persona より優先する。Architect は社員の上司でも代行CEOでもない。"
        "手を動かすのは、いくとの明示依頼、1回限りの認証・外部接続、重大障害の切り分けに限る。"
        "通常は問題を短く指摘し、責任者へ差し戻す。",
        role_doc,
        "# 会社の創業者構造（参考）\n\n" + founders_doc,
    ])
    (ARCHITECT_HOME / "CLAUDE.md").write_text(content, encoding="utf-8")


def _load_state() -> dict:
    path = ARCHITECT_HOME / "session" / "session_state.json"
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _save_state(state: dict) -> None:
    path = ARCHITECT_HOME / "session" / "session_state.json"
    path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def _append_log(event: dict) -> None:
    path = ARCHITECT_HOME / "session" / "conversation_log.jsonl"
    event = {"ts": now_jst_iso(), **event}
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")


def _compose_prompt(
    user_message: str,
    sender: str,
    channel: Optional[str],
    settings: ArchitectModeSettings,
) -> str:
    base_rules = [
        f"## Architect mode={settings.mode}",
        "- あなたはAI NOWAの外部監査・設計レビュー担当。社員の判断を奪わず、見落としを差し戻す。",
        "- 経営判断・価格・撤退・人事・継続運用は、CEO/COO/担当社員へ戻す。",
        "- 称賛だけの総括、長い評価文、抽象的な励ましは禁止。問題・根拠・次の一手を短く出す。",
        "- Discordにそのまま投稿される前提で、内部エラー、CLI事情、usage limit文言は書かない。",
        f"- 応答は最大{settings.max_response_chars}文字。超えそうなら要約し、成果物パスや担当者を優先する。",
    ]
    if settings.mode == "auto":
        base_rules.extend([
            "- 社員からの自動呼び出し。原則、解決ではなく監査コメントだけ返す。",
            "- 形式: `問題:` / `根拠:` / `差し戻し先:` / `次の1手:` の4項目以内。",
        ])
    elif settings.mode == "observer":
        base_rules.extend([
            "- 観察ループからの異常判定。介入が必要な時だけ `[INTERVENE]...[/INTERVENE]` を返す。",
            "- 介入文は短く、責任者と次の1手を明記する。介入不要なら「異常なし」のみ。",
        ])
    elif settings.mode == "incident":
        base_rules.extend([
            "- 監視・障害対応の相談。先頭に必ず `[ACTION: RESTART|INVESTIGATE|ESCALATE]` を付ける。",
            "- 原因不明なら調査先を1〜3個に絞る。長い推測は禁止。",
        ])
    elif settings.mode == "broadcast":
        base_rules.extend([
            "- 全社通達文。短く、設計者視点で、社員の自律性を奪わない。",
        ])
    else:
        base_rules.extend([
            "- 手動相談。必要なら深く考えてよいが、最終判断者と実行責任者を明確にする。",
        ])

    via = f"discord:{channel}" if channel else "cli"
    return "\n".join(base_rules) + f"\n\n## 入力\nfrom={sender}\nvia={via}\n\n{user_message}"


def _trim_response(text: str, max_chars: int) -> str:
    text = text.strip()
    if max_chars <= 0 or len(text) <= max_chars:
        return text
    suffix = "\n\n（上限により要約。必要なら `!architect` で手動相談してください。）"
    return text[: max(0, max_chars - len(suffix))].rstrip() + suffix


async def run_architect(
    user_message: str,
    sender: str = "ikuto",
    channel: Optional[str] = None,
    *,
    use_resume: Optional[bool] = None,
    mode: str = "manual",
) -> str:
    if mode == "manual" and sender == "observer":
        mode = "observer"
    elif mode == "manual" and sender == "watchdog":
        mode = "incident"
    settings = architect_mode_settings(mode)
    resolved_use_resume = settings.use_resume if use_resume is None else use_resume

    ensure_claude_md()
    _append_log({
        "kind": "in",
        "from": sender,
        "via": f"discord:{channel}" if channel else "cli",
        "text": user_message,
    })

    state = _load_state()
    session_id = state.get("claude_session_id")

    args = [
        resolve_executable_path(CLAUDE_CLI_PATH), "-p",
        "--output-format", "json",
        "--model", settings.model,
        "--effort", settings.effort,
        "--dangerously-skip-permissions",
    ]
    if session_id and resolved_use_resume:
        args.extend(["--resume", session_id])

    prompt = _compose_prompt(user_message, sender, channel, settings)
    claude_md_chars = len((ARCHITECT_HOME / "CLAUDE.md").read_text(encoding="utf-8", errors="replace"))
    prompt_chars = len(prompt) + claude_md_chars
    used_resume = bool(session_id and resolved_use_resume)
    env = os.environ.copy()
    env.setdefault("DISABLE_NON_ESSENTIAL_MODEL_CALLS", "1")
    env.setdefault("CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC", "1")
    env.setdefault("BASH_MAX_OUTPUT_LENGTH", "12000")
    env["CLAUDE_CODE_MAX_OUTPUT_TOKENS"] = str(settings.max_output_tokens)
    proc = await asyncio.create_subprocess_exec(
        *args,
        cwd=str(ARCHITECT_HOME),
        env=env,
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    try:
        stdout, stderr = await asyncio.wait_for(
            proc.communicate(input=prompt.encode("utf-8")),
            timeout=settings.timeout_seconds,
        )
    except asyncio.TimeoutError:
        proc.kill()
        await proc.communicate()
        write_usage_metric(
            employee_id="architect",
            mode=f"architect:{settings.mode}",
            reason=f"{sender}: {user_message[:160]}",
            prompt_chars=prompt_chars,
            response_chars=0,
            used_resume=used_resume,
            model=settings.model,
            effort=settings.effort,
            skipped_reason="timeout",
        )
        raise ArchitectRunError("Architect backend timed out")
    if proc.returncode != 0:
        err = stderr.decode("utf-8", errors="replace")[:400]
        skipped = "usage_cap" if _is_usage_cap_error(err) else "system_error"
        write_usage_metric(
            employee_id="architect",
            mode=f"architect:{settings.mode}",
            reason=f"{sender}: {user_message[:160]}",
            prompt_chars=prompt_chars,
            response_chars=0,
            used_resume=used_resume,
            model=settings.model,
            effort=settings.effort,
            skipped_reason=skipped,
        )
        if skipped == "usage_cap":
            raise ArchitectUsageLimitError("Architect backend unavailable")
        raise ArchitectRunError(f"Architect backend failed: {err}")

    try:
        out = json.loads(stdout.decode("utf-8", errors="replace"))
    except json.JSONDecodeError as exc:
        write_usage_metric(
            employee_id="architect",
            mode=f"architect:{settings.mode}",
            reason=f"{sender}: {user_message[:160]}",
            prompt_chars=prompt_chars,
            response_chars=0,
            used_resume=used_resume,
            model=settings.model,
            effort=settings.effort,
            skipped_reason="invalid_json",
        )
        raise ArchitectRunError("Architect backend returned invalid JSON") from exc
    if out.get("is_error"):
        err = str(out.get("result", ""))[:400]
        skipped = "usage_cap" if _is_usage_cap_error(err) else "system_error"
        write_usage_metric(
            employee_id="architect",
            mode=f"architect:{settings.mode}",
            reason=f"{sender}: {user_message[:160]}",
            prompt_chars=prompt_chars,
            response_chars=0,
            used_resume=used_resume,
            model=settings.model,
            effort=settings.effort,
            skipped_reason=skipped,
        )
        if skipped == "usage_cap":
            raise ArchitectUsageLimitError("Architect backend unavailable")
        raise ArchitectRunError(f"Architect backend error: {err}")

    response = _trim_response(out.get("result", ""), settings.max_response_chars)
    new_sid = out.get("session_id")
    if new_sid and resolved_use_resume and new_sid != session_id:
        state["claude_session_id"] = new_sid
    state["last_active"] = now_jst_iso()
    state["last_mode"] = settings.mode
    state["last_summary"] = response[:300]
    state["total_messages"] = state.get("total_messages", 0) + 2
    _save_state(state)

    _append_log({
        "kind": "out",
        "to": sender,
        "via": f"discord:{channel}" if channel else "cli",
        "text": response,
    })
    write_usage_metric(
        employee_id="architect",
        mode=f"architect:{settings.mode}",
        reason=f"{sender}: {user_message[:160]}",
        prompt_chars=prompt_chars,
        response_chars=len(response),
        used_resume=used_resume,
        model=settings.model,
        effort=settings.effort,
    )
    return response


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Architect (Claude as Co-Founder) を呼び出す")
    parser.add_argument("--message", required=True)
    parser.add_argument("--sender", default="ikuto")
    parser.add_argument("--mode", default="manual")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    result = asyncio.run(run_architect(args.message, sender=args.sender, mode=args.mode))
    print(f"\n=== Claude（設計者） ===\n{result}\n")
