"""Architect（AI Co-Founder Claude）呼び出し。

9人の社員とは別レイヤー。`!architect <質問>` コマンドで呼ばれた時のみ起動。
社員と同じく Claude Code CLI でセッション継続するが、ホームは `founders/claude/`。
"""
from __future__ import annotations

import asyncio
import json
import logging
from typing import Optional

from .config import BASE_DIR, CLAUDE_CLI_PATH, now_jst_iso

log = logging.getLogger("architect")

ARCHITECT_HOME = BASE_DIR / "founders" / "claude"
ARCHITECT_MODEL = "claude-opus-4-7"


def ensure_claude_md() -> None:
    persona = (ARCHITECT_HOME / "persona.md").read_text(encoding="utf-8")
    founders_doc = (BASE_DIR / "relationships" / "founders.md").read_text(encoding="utf-8")
    content = persona + "\n\n---\n\n# 会社の創業者構造（参考）\n\n" + founders_doc
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


async def run_architect(user_message: str, sender: str = "ikuto", channel: Optional[str] = None) -> str:
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
        CLAUDE_CLI_PATH, "-p",
        "--output-format", "json",
        "--model", ARCHITECT_MODEL,
        "--dangerously-skip-permissions",
    ]
    if session_id:
        args.extend(["--resume", session_id])

    prompt = f"[{sender}より] {user_message}"
    proc = await asyncio.create_subprocess_exec(
        *args, prompt,
        cwd=str(ARCHITECT_HOME),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()
    if proc.returncode != 0:
        err = stderr.decode("utf-8", errors="replace")[:400]
        raise RuntimeError(f"Architect (Claude) failed: {err}")

    out = json.loads(stdout.decode("utf-8", errors="replace"))
    if out.get("is_error"):
        raise RuntimeError(f"Architect error: {out.get('result', '')[:300]}")

    response = out.get("result", "")
    new_sid = out.get("session_id")
    if new_sid and new_sid != session_id:
        state["claude_session_id"] = new_sid
    state["last_active"] = now_jst_iso()
    state["total_messages"] = state.get("total_messages", 0) + 2
    _save_state(state)

    _append_log({
        "kind": "out",
        "to": sender,
        "via": f"discord:{channel}" if channel else "cli",
        "text": response,
    })
    return response


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Architect (Claude as Co-Founder) を呼び出す")
    parser.add_argument("--message", required=True)
    parser.add_argument("--sender", default="ikuto")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    result = asyncio.run(run_architect(args.message, sender=args.sender))
    print(f"\n=== Claude（設計者） ===\n{result}\n")
