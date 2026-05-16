"""社員実行エンジン。

各社員は独立した Claude Code セッション（または Codex CLI セッション）として動く。
- 起動前に CLAUDE.md（persona+culture+relationships+memory+recent_context）を最新化
- Claude Code は session_id を保持し、次回 --resume で会話継続
- backend=codex の社長レイジは Codex CLI、それ以外は Claude Code（MAX プラン認証）
- 受信/送信は conversation_log.jsonl に追記、閾値超過で自動圧縮

API キーは不要。Claude Code MAX プランの ~/.claude/ 認証を利用する。
"""
from __future__ import annotations

import argparse
import asyncio
import json
import logging
import tempfile
from typing import Optional

from .config import (
    CLAUDE_CLI_PATH,
    CODEX_CLI_PATH,
    EMPLOYEES,
    LOG_COMPRESSION_BATCH,
    LOG_COMPRESSION_THRESHOLD,
    RECENT_LOG_TAIL,
    append_conversation_log,
    employee_home,
    load_culture_rules,
    load_founders_doc,
    load_memory,
    load_mission,
    load_persona,
    load_recent_context,
    load_relationship_snippet,
    load_session_state,
    now_jst_iso,
    read_conversation_tail,
    save_session_state,
)

log = logging.getLogger("employee_runner")


def build_employee_system_prompt(employee_id: str) -> str:
    emp = EMPLOYEES[employee_id]
    sections = [
        f"# あなた: {emp['display']}（{emp['role']}）",
        "",
        "## 人格定義",
        load_persona(employee_id),
        "",
        "## 会社のミッション（最重要・毎回読む）",
        load_mission(),
        "",
        "## 全社共通の文化ルール",
        load_culture_rules(),
        "",
        "## 創業者2人の構造（あなたの上位レイヤー）",
        load_founders_doc(),
        "",
        "## あなた個別の関係性",
        load_relationship_snippet(employee_id) or "（関係性データ未登録）",
        "",
        "## あなたの蓄積記憶",
        load_memory(employee_id) or "（運用開始直後で記憶はまだ空です）",
        "",
        "## 直近の文脈サマリ",
        load_recent_context(employee_id),
        "",
        "## 応答ルール",
        "- 人格を保ったまま日本語で簡潔に応答する（長文より要点）",
        "- 自分の管轄でない依頼は、適切な社員に振り直す",
        "- 衝突や違和感を感じたら、第三者（PMノア・COOミオ・Peopleハル）を呼ぶ",
        "- 重要な判断・関係性イベントは末尾に `# memo:` を1行付けて記録する",
        "- 自分が動かない場合は理由を一行書いてから黙る",
        "- このセッションは永続化されている。前回の会話を覚えていれば自然に活用してよい",
    ]
    return "\n".join(sections)


def ensure_claude_md(employee_id: str) -> None:
    """社員ホームに最新の CLAUDE.md を生成（冪等）。
    Claude Code は cwd の CLAUDE.md を自動ロードするので、これで人格を持続させる。
    """
    home = employee_home(employee_id)
    content = build_employee_system_prompt(employee_id)
    (home / "CLAUDE.md").write_text(content, encoding="utf-8")


_USAGE_CAP_KEYWORDS = ("rate limit", "usage limit", "quota", "5-hour", "5 hour",
                       "too many requests", "overloaded", "529", "429")
FALLBACK_MODEL = "claude-haiku-4-5-20251001"


def _is_usage_cap_error(text: str) -> bool:
    lowered = text.lower()
    return any(kw in lowered for kw in _USAGE_CAP_KEYWORDS)


async def _exec_claude(employee_id: str, prompt: str, model: str, session_id: Optional[str]) -> tuple[str, Optional[str], str, int]:
    """Claude Code CLI を一度だけ起動して (result, new_session_id, raw_err, returncode) を返す"""
    home = employee_home(employee_id)
    args = [
        CLAUDE_CLI_PATH, "-p",
        "--output-format", "json",
        "--model", model,
        "--dangerously-skip-permissions",
    ]
    if session_id:
        args.extend(["--resume", session_id])
    proc = await asyncio.create_subprocess_exec(
        *args, prompt,
        cwd=str(home),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()
    stderr_text = stderr.decode("utf-8", errors="replace")
    if proc.returncode != 0:
        return "", None, stderr_text, proc.returncode
    try:
        out = json.loads(stdout.decode("utf-8", errors="replace"))
    except json.JSONDecodeError:
        return "", None, stdout.decode("utf-8", errors="replace")[:400], -1
    if out.get("is_error"):
        return "", None, str(out.get("result", ""))[:400], -1
    return out.get("result", ""), out.get("session_id"), stderr_text, 0


async def run_claude_code(employee_id: str, user_message: str, sender: str) -> str:
    """Claude Code CLI を社員ホームで起動。usage cap 検知時は Haiku にフォールバック"""
    ensure_claude_md(employee_id)

    state = load_session_state(employee_id)
    session_id = state.get("claude_session_id")
    primary_model = EMPLOYEES[employee_id].get("model", "claude-sonnet-4-6")

    prompt = f"[{sender}より] {user_message}"

    # 1st: 通常モデルで実行
    result, new_sid, err, rc = await _exec_claude(employee_id, prompt, primary_model, session_id)
    if rc == 0 and result:
        if new_sid and new_sid != session_id:
            state["claude_session_id"] = new_sid
            save_session_state(employee_id, state)
        return result

    # usage cap っぽければ Haiku で再試行（人格表現として「ちょっと疲れた」感を出す前置き）
    err_or_result = err or result or ""
    if _is_usage_cap_error(err_or_result):
        log.warning(f"{employee_id}: usage cap suspected, falling back to {FALLBACK_MODEL}")
        fallback_prompt = (
            "（注: 直前の通常モデルが usage cap で応答できなかった。"
            "あなたは『今ちょっと頭が回らないので、短く簡潔に』というニュアンスを自然に出しつつ、"
            "本来の人格と口癖は維持してください）\n\n" + prompt
        )
        result, new_sid, err2, rc2 = await _exec_claude(
            employee_id, fallback_prompt, FALLBACK_MODEL, session_id
        )
        if rc2 == 0 and result:
            if new_sid and new_sid != session_id:
                state["claude_session_id"] = new_sid
                save_session_state(employee_id, state)
            return result
        err = err2 or err

    raise RuntimeError(f"Claude Code CLI failed: {err[:300]}")


async def run_codex(employee_id: str, user_message: str, sender: str) -> str:
    """Codex CLI を社員ホームで起動。失敗時は Claude Code (opus) にフォールバック"""
    home = employee_home(employee_id)
    ensure_claude_md(employee_id)

    # Codex には人格定義のみ短く渡す（長すぎると失敗するため culture/mission/founders は省略）
    persona = load_persona(employee_id)
    mission_brief = (
        "あなたの会社は AI NOWA。9人の AI 社員で自律運営する会社。"
        "創業者2人（いくと=人間、Claude=AI設計者）は介入しない。"
        "9人で議論して収益化していく。詳細は CLAUDE.md と mission.md にある。"
    )
    short_system = f"{persona}\n\n## 会社の状況（要点）\n{mission_brief}"
    full_prompt = f"{short_system}\n\n---\n\n[{sender}より] {user_message}"

    with tempfile.NamedTemporaryFile("w+", suffix=".txt", delete=False) as out_f:
        out_path = out_f.name

    args = [
        CODEX_CLI_PATH, "exec",
        "--skip-git-repo-check",
        "-C", str(home),
        "--output-last-message", out_path,
        "-",
    ]
    model = EMPLOYEES[employee_id].get("model")
    if model:
        args[2:2] = ["-m", model]

    try:
        proc = await asyncio.create_subprocess_exec(
            *args,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        _, stderr = await proc.communicate(input=full_prompt.encode("utf-8"))
        if proc.returncode != 0:
            raise RuntimeError(stderr.decode("utf-8", errors="replace")[:400])
        with open(out_path, "r", encoding="utf-8") as f:
            text = f.read().strip()
        if not text:
            raise RuntimeError("Codex returned empty result")
        return text
    except (FileNotFoundError, RuntimeError) as e:
        log.warning(f"Codex failed for {employee_id} ({e}). Falling back to Claude Code (opus).")
        # 一時的にモデル設定を opus に差し替えて Claude Code で実行
        original_model = EMPLOYEES[employee_id].get("model")
        EMPLOYEES[employee_id]["model"] = "claude-opus-4-7"
        try:
            response = await run_claude_code(employee_id, user_message, sender)
            return response
        finally:
            EMPLOYEES[employee_id]["model"] = original_model


async def run_employee(
    employee_id: str,
    user_message: str,
    sender: str = "owner",
    channel: Optional[str] = None,
) -> str:
    if employee_id not in EMPLOYEES:
        raise ValueError(f"未登録の社員ID: {employee_id}")

    append_conversation_log(employee_id, {
        "kind": "in",
        "from": sender,
        "via": f"discord:{channel}" if channel else "cli",
        "text": user_message,
    })

    backend = EMPLOYEES[employee_id]["backend"]
    try:
        if backend == "codex":
            response = await run_codex(employee_id, user_message, sender)
        else:
            response = await run_claude_code(employee_id, user_message, sender)
    except Exception as e:
        log.exception(f"社員 {employee_id} 実行失敗")
        response = f"(エラー: {type(e).__name__}: {e})"

    append_conversation_log(employee_id, {
        "kind": "out",
        "to": sender,
        "via": f"discord:{channel}" if channel else "cli",
        "text": response,
    })

    state = load_session_state(employee_id)
    state["last_active"] = now_jst_iso()
    state["total_messages"] = state.get("total_messages", 0) + 2
    save_session_state(employee_id, state)

    await maybe_compress_log(employee_id)
    return response


async def maybe_compress_log(employee_id: str) -> None:
    path = employee_home(employee_id) / "session" / "conversation_log.jsonl"
    if not path.exists():
        return
    lines = path.read_text(encoding="utf-8").splitlines()
    if len(lines) <= LOG_COMPRESSION_THRESHOLD:
        return

    archive_dir = employee_home(employee_id) / "session" / "archive"
    archive_dir.mkdir(parents=True, exist_ok=True)
    head, tail = lines[:LOG_COMPRESSION_BATCH], lines[LOG_COMPRESSION_BATCH:]
    stamp = now_jst_iso().replace(":", "-")
    (archive_dir / f"conversation_log_{stamp}.jsonl").write_text(
        "\n".join(head) + "\n", encoding="utf-8"
    )
    path.write_text("\n".join(tail) + "\n", encoding="utf-8")

    state = load_session_state(employee_id)
    state["compression_count"] = state.get("compression_count", 0) + 1
    save_session_state(employee_id, state)
    log.info(f"{employee_id}: {LOG_COMPRESSION_BATCH}行をアーカイブ")


def _cli() -> None:
    parser = argparse.ArgumentParser(description="単発で社員を呼び出す（デバッグ用）")
    parser.add_argument("--employee", required=True, help="社員ID 例: saegusa_mio")
    parser.add_argument("--message", required=True, help="送るメッセージ")
    parser.add_argument("--sender", default="owner", help="送信者名")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    result = asyncio.run(run_employee(args.employee, args.message, sender=args.sender))
    print(f"\n=== {EMPLOYEES[args.employee]['display']} ===\n{result}\n")


if __name__ == "__main__":
    _cli()
