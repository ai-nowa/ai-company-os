"""社員実行エンジン。

各社員は独立した Claude Code セッション（または Codex CLI セッション）として動く。
- CLAUDE.md は最小人格・不変ルールだけを保持
- 動的情報は state_digest として毎回の prompt に渡す
- Claude Code/Codex の model effort は mode・sender・役割で切り替える
- backend=codex の社長レイジは Codex CLI、それ以外は Claude Code（MAX プラン認証）
- 受信/送信は conversation_log.jsonl に追記、閾値超過で自動圧縮

API キーは不要。Claude Code MAX プランの ~/.claude/ 認証を利用する。
"""
from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import tempfile
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional

from .config import (
    CLAUDE_CLI_PATH,
    CODEX_CLI_PATH,
    EMPLOYEES,
    LOG_COMPRESSION_BATCH,
    LOG_COMPRESSION_THRESHOLD,
    append_conversation_log,
    employee_home,
    COMPANY_DIR,
    load_persona,
    load_relationship_snippet,
    load_session_state,
    now_jst_iso,
    save_session_state,
)
from .context_assembler import assemble_state_digest, write_usage_metric
from . import dynamic_config
from .model_policy import (
    FRESH_ROUTINE_SENDERS,
    ModelRoute,
    RUN_MODES,
    needs_executive_model,
    resolve_model_route,
)

log = logging.getLogger("employee_runner")

# 同時実行制限（Claude/Codex 子プロセスの並列度上限） - usage 節約
_concurrency_semaphore = asyncio.Semaphore(2)

RESUME_MODES = {"work", "executive"}
CIRCUIT_SKIP_MODES = {"micro", "routine"}
CIRCUIT_STATE_PATH = COMPANY_DIR / ".llm_circuit_state.json"
DEFAULT_CLAUDE_CIRCUIT_COOLDOWN_MINUTES = 15
DEFAULT_CLAUDE_CIRCUIT_FAILURE_THRESHOLD = 2
DEFAULT_CLAUDE_CIRCUIT_WINDOW_MINUTES = 10


@dataclass
class EmployeeRunResult:
    ok: bool
    text: str = ""
    employee_id: str = ""
    mode: str = "routine"
    reason: str = ""
    prompt_chars: int = 0
    response_chars: int = 0
    used_resume: bool = False
    model: Optional[str] = None
    effort: Optional[str] = None
    route_tier: Optional[str] = None
    route_reason: Optional[str] = None
    route_escalated: Optional[bool] = None
    fallback_model: Optional[str] = None
    chain_id: Optional[str] = None
    depth: Optional[int] = None
    skipped_reason: Optional[str] = None
    system_error: Optional[str] = None


def build_employee_system_prompt(employee_id: str) -> str:
    emp = EMPLOYEES[employee_id]

    channels = emp.get("default_channels", [])
    channel_summary = "全チャンネル（People担当）" if "all" in channels else " / ".join(channels)

    sections = [
        f"# あなた: {emp['display']}（{emp['role']}）",
        "",
        "## 人格定義",
        load_persona(employee_id),
        "",
        "## 行動原則（共通）",
        "- state_digestを常に優先。routine=最小読込、work=必要なら読む",
        "- @付きメンション必須。<!-- META: thread=\"名前\", invite=\"id\" -->でスレッド作成",
        "- 重要判断は末尾に # memo: 記録。待ち中は別タスクへ。同じ話題を24h内に繰り返さない",
        "- due/期限/判定日/観察日は待機日ではなく最遅締切。未来日でも今できる準備・草稿・検証・依頼整理を進める",
        "- 「○日まで待つ」だけで終えない。待つ必要がある時も next_action_now と並行タスクを出す",
        "- 権限/認証/秘密/公開/決済/削除/本番/外部投稿は、先にリスク・代替案・監査要否を短く確認する",
        "",
        "## あなた個別の関係性",
        load_relationship_snippet(employee_id) or "（関係性データ未登録）",
        "",
        "## 基本アクセス範囲",
        f"- default_channels: {channel_summary or '未設定'}",
    ]
    return "\n".join(sections)


def ensure_claude_md(employee_id: str) -> None:
    """社員ホームに最新の CLAUDE.md を生成（冪等）。
    Claude Code は cwd の CLAUDE.md を自動ロードするので、これで人格を持続させる。
    """
    home = employee_home(employee_id)
    content = build_employee_system_prompt(employee_id)
    path = home / "CLAUDE.md"
    if path.exists() and path.read_text(encoding="utf-8", errors="replace") == content:
        return
    path.write_text(content, encoding="utf-8")


def _claude_md_chars(employee_id: str) -> int:
    path = employee_home(employee_id) / "CLAUDE.md"
    try:
        return len(path.read_text(encoding="utf-8", errors="replace"))
    except OSError:
        return 0


_USAGE_CAP_KEYWORDS = ("rate limit", "usage limit", "quota", "5-hour", "5 hour",
                       "too many requests", "overloaded", "529", "429")
FALLBACK_MODEL = "claude-haiku-4-5-20251001"


def _is_usage_cap_error(text: str) -> bool:
    lowered = text.lower()
    return any(kw in lowered for kw in _USAGE_CAP_KEYWORDS)


def _load_circuit_state() -> dict:
    try:
        return json.loads(CIRCUIT_STATE_PATH.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _save_circuit_state(state: dict) -> None:
    COMPANY_DIR.mkdir(parents=True, exist_ok=True)
    CIRCUIT_STATE_PATH.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def _parse_iso_datetime(value: str) -> Optional[datetime]:
    try:
        return datetime.fromisoformat(value)
    except (TypeError, ValueError):
        return None


def _circuit_enabled() -> bool:
    value = dynamic_config.get("llm_circuit.enabled", True)
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    return bool(value)


def _claude_circuit_cooldown_minutes() -> int:
    try:
        return int(dynamic_config.get(
            "llm_circuit.claude_cooldown_minutes",
            DEFAULT_CLAUDE_CIRCUIT_COOLDOWN_MINUTES,
        ))
    except (TypeError, ValueError):
        return DEFAULT_CLAUDE_CIRCUIT_COOLDOWN_MINUTES


def _circuit_skip_reason(mode: str, backend: str) -> Optional[str]:
    if not _circuit_enabled():
        return None
    if mode not in CIRCUIT_SKIP_MODES:
        return None
    # Claude Code の一時停止で Codex 社員まで止めない。
    if backend != "claude":
        return None
    state = _load_circuit_state()
    circuit = (state.get("circuits") or {}).get(backend, {})
    open_until = circuit.get("open_until")
    reason = circuit.get("reason", "llm circuit open")

    # 旧フォーマット互換: 以前は単一の global circuit だった。
    # ただし新しい短い cooldown を適用し、古い90分停止を引きずらない。
    if not open_until and backend == "claude":
        open_until = state.get("open_until")
        reason = state.get("reason", reason)
        updated_at = _parse_iso_datetime(state.get("updated_at", ""))
        legacy_until = _parse_iso_datetime(open_until) if open_until else None
        if updated_at and legacy_until:
            capped_until = updated_at + timedelta(minutes=_claude_circuit_cooldown_minutes())
            if capped_until < legacy_until:
                open_until = capped_until.isoformat(timespec="seconds")

    if not open_until:
        return None
    until = _parse_iso_datetime(open_until)
    if until is None:
        return None
    if datetime.now(until.tzinfo) >= until:
        return None
    return f"{reason}; retry_after={open_until}"


def _open_circuit(backend: str, minutes: int, reason: str) -> None:
    from .config import JST

    until = datetime.now(JST) + timedelta(minutes=minutes)
    state = _load_circuit_state()
    circuits = state.setdefault("circuits", {})
    circuits[backend] = {
        "open_until": until.isoformat(timespec="seconds"),
        "reason": reason,
        "updated_at": now_jst_iso(),
    }
    state["updated_at"] = now_jst_iso()
    _save_circuit_state(state)
    log.warning("%s LLM circuit opened for %d minutes: %s", backend, minutes, reason)


def _record_claude_failure_and_maybe_open(reason: str) -> bool:
    from .config import JST

    try:
        threshold = int(dynamic_config.get(
            "llm_circuit.claude_failure_threshold",
            DEFAULT_CLAUDE_CIRCUIT_FAILURE_THRESHOLD,
        ))
    except (TypeError, ValueError):
        threshold = DEFAULT_CLAUDE_CIRCUIT_FAILURE_THRESHOLD
    try:
        window_minutes = int(dynamic_config.get(
            "llm_circuit.claude_failure_window_minutes",
            DEFAULT_CLAUDE_CIRCUIT_WINDOW_MINUTES,
        ))
    except (TypeError, ValueError):
        window_minutes = DEFAULT_CLAUDE_CIRCUIT_WINDOW_MINUTES

    state = _load_circuit_state()
    now = datetime.now(JST)
    cutoff = now - timedelta(minutes=window_minutes)
    events = []
    for event in state.get("failure_events", {}).get("claude", []):
        ts = _parse_iso_datetime(event.get("ts", ""))
        if ts and ts >= cutoff:
            events.append(event)
    events.append({"ts": now.isoformat(timespec="seconds"), "reason": reason[:180]})
    state.setdefault("failure_events", {})["claude"] = events[-20:]
    state["updated_at"] = now_jst_iso()
    _save_circuit_state(state)

    if len(events) >= threshold:
        _open_circuit("claude", _claude_circuit_cooldown_minutes(), reason)
        return True
    log.warning(
        "Claude failure recorded without opening circuit: %d/%d in %dmin: %s",
        len(events),
        threshold,
        window_minutes,
        reason,
    )
    return False


def _mode_rules(mode: str) -> str:
    if mode == "micro":
        return (
            "## mode=micro\n"
            "- 300文字以内。雑談・heartbeat・軽い確認だけ。\n"
            "- ファイルは原則読まない。state_digestだけで返す。\n"
            "- 成果物作成や広範囲調査が必要なら、次回work依頼に回す。"
        )
    if mode == "routine":
        return (
            "## mode=routine\n"
            "- 800文字以内。通常の社員応答。\n"
            "- state_digestと継続記憶を優先し、大きなログ・全ディレクトリ走査はしない。\n"
            "- Discord投稿は要約と必要な成果物パスを優先する。"
        )
    if mode == "executive":
        return (
            "## mode=executive\n"
            "- 重要判断モード。必要な根拠を短く整理して判断する。\n"
            "- 意思決定、リスク、次の担当者を明確にする。"
        )
    return (
        "## mode=work\n"
        "- 実装・台本・設計などの作業モード。\n"
        "- 必要なファイルだけ読み、成果物ファイルパスと要約を残す。"
    )


def _infer_mode(sender: str, user_message: str, mode: Optional[str]) -> str:
    if mode in RUN_MODES:
        resolved = mode
    elif sender == "heartbeat":
        resolved = "micro"
    elif sender == "self_loop":
        resolved = "routine"
    else:
        resolved = "routine"
    if (
        resolved != "micro"
        and sender not in FRESH_ROUTINE_SENDERS
        and needs_executive_model(user_message)
    ):
        return "executive"
    return resolved


def _compose_prompt(employee_id: str, user_message: str, sender: str, mode: str, reason: str) -> str:
    digest = assemble_state_digest(employee_id, reason or user_message, mode=mode)
    return "\n\n".join([
        digest,
        _mode_rules(mode),
        "## 今回の入力",
        f"[{sender}より] {user_message}",
    ])


def _should_use_resume(mode: str, sender: str, reason: str, user_message: str) -> bool:
    if mode in RESUME_MODES:
        return True
    if mode != "routine":
        return False
    if sender in FRESH_ROUTINE_SENDERS:
        return False
    # 人間からの依頼や社員間の実会話は、継続性が品質に直結するので resume を許可する。
    return True


def _allowed_dirs_for_mode(employee_id: str, mode: str) -> list[str]:
    from .config import BASE_DIR

    if mode == "micro":
        return []
    if mode == "routine":
        return [str(BASE_DIR / "company")]
    shared_dirs = [
        str(BASE_DIR / "shared"),
        str(BASE_DIR / "company"),
        str(BASE_DIR / "relationships"),
    ]
    for other_emp in EMPLOYEES.keys():
        if other_emp != employee_id:
            shared_dirs.append(str(employee_home(other_emp) / "outbox"))
    return shared_dirs


async def _exec_claude(
    employee_id: str,
    prompt: str,
    model: str,
    effort: str,
    session_id: Optional[str],
    mode: str,
    fallback_model: Optional[str] = None,
    max_output_tokens: Optional[int] = None,
) -> tuple[str, Optional[str], str, int]:
    """Claude Code CLI を一度だけ起動して (result, new_session_id, raw_err, returncode) を返す"""
    home = employee_home(employee_id)

    args = [
        CLAUDE_CLI_PATH, "-p",
        "--output-format", "json",
        "--model", model,
        "--effort", effort,
        "--dangerously-skip-permissions",
    ]
    if fallback_model:
        args.extend(["--fallback-model", fallback_model])
    for d in _allowed_dirs_for_mode(employee_id, mode):
        args.extend(["--add-dir", d])
    if session_id:
        args.extend(["--resume", session_id])
    # prompt は stdin 経由で渡す（--add-dir が貪欲に positional 引数を吸収する問題を回避）
    env = os.environ.copy()
    env.setdefault("DISABLE_NON_ESSENTIAL_MODEL_CALLS", "1")
    env.setdefault("CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC", "1")
    env.setdefault("BASH_MAX_OUTPUT_LENGTH", "12000")
    if max_output_tokens:
        env["CLAUDE_CODE_MAX_OUTPUT_TOKENS"] = str(max_output_tokens)

    proc = await asyncio.create_subprocess_exec(
        *args,
        cwd=str(home),
        env=env,
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate(input=prompt.encode("utf-8"))
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


async def run_claude_code(
    employee_id: str,
    prompt: str,
    mode: str,
    use_resume: bool,
    route: ModelRoute,
) -> tuple[str, bool]:
    """Claude Code CLI を社員ホームで起動。usage cap 検知時は Haiku にフォールバック"""
    state = load_session_state(employee_id)
    raw_session_id = state.get("claude_session_id")
    session_id = raw_session_id if use_resume else None
    used_resume = bool(session_id)
    primary_model = route.model

    # 1st: 通常モデルで実行
    result, new_sid, err, rc = await _exec_claude(
        employee_id,
        prompt,
        primary_model,
        route.effort,
        session_id,
        mode,
        fallback_model=route.fallback_model,
        max_output_tokens=route.max_output_tokens,
    )
    if rc == 0 and result:
        if new_sid and new_sid != session_id:
            state["claude_session_id"] = new_sid
            save_session_state(employee_id, state)
        return result, used_resume

    err_or_result = err or result or ""
    usage_like = _is_usage_cap_error(err_or_result) or (rc == 1 and not err_or_result.strip())
    if usage_like:
        _record_claude_failure_and_maybe_open(
            f"Claude Code unavailable ({err_or_result[:120] or 'rc=1/no stderr'})"
        )

    # usage cap っぽい時の再試行は deep work だけ。routine/micro では二重消費を避ける。
    if usage_like and mode in RESUME_MODES:
        fallback_model = route.fallback_model or FALLBACK_MODEL
        log.warning(f"{employee_id}: usage cap suspected, falling back to {fallback_model}")
        fallback_prompt = (
            "（注: 直前の通常モデルが usage cap で応答できなかった。"
            "あなたは『今ちょっと頭が回らないので、短く簡潔に』というニュアンスを自然に出しつつ、"
            "本来の人格と口癖は維持してください）\n\n" + prompt
        )
        result, new_sid, err2, rc2 = await _exec_claude(
            employee_id,
            fallback_prompt,
            fallback_model,
            "low",
            session_id,
            mode,
            fallback_model=None,
            max_output_tokens=route.max_output_tokens,
        )
        if rc2 == 0 and result:
            if new_sid and new_sid != session_id:
                state["claude_session_id"] = new_sid
                save_session_state(employee_id, state)
            return result, used_resume
        err = err2 or err
        rc = rc2

    if not err:
        log.error(
            "CLI 終了（stderr 空）: rc=%d, employee=%s, model=%s, effort=%s",
            rc, employee_id, primary_model, route.effort,
        )
    raise RuntimeError(f"Claude Code CLI failed (rc={rc}): {err[:300] or '(no stderr)'}")


async def run_codex(employee_id: str, prompt: str, route: ModelRoute) -> str:
    """Codex CLI を社員ホームで起動。失敗時の二重LLMフォールバックはしない。"""
    home = employee_home(employee_id)

    with tempfile.NamedTemporaryFile("w+", suffix=".txt", delete=False) as out_f:
        out_path = out_f.name

    args = [
        CODEX_CLI_PATH, "exec",
        "--skip-git-repo-check",
        "-C", str(home),
        "--output-last-message", out_path,
        "-",
    ]
    if route.model:
        args[2:2] = [
            "-m", route.model,
            "-c", f'model_reasoning_effort="{route.effort}"',
        ]

    try:
        proc = await asyncio.create_subprocess_exec(
            *args,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        _, stderr = await proc.communicate(input=prompt.encode("utf-8"))
        if proc.returncode != 0:
            raise RuntimeError(stderr.decode("utf-8", errors="replace")[:400])
        with open(out_path, "r", encoding="utf-8") as f:
            text = f.read().strip()
        if not text:
            raise RuntimeError("Codex returned empty result")
        return text
    finally:
        import os
        try:
            os.unlink(out_path)
        except OSError:
            pass


async def run_employee_result(
    employee_id: str,
    user_message: str,
    sender: str = "owner",
    channel: Optional[str] = None,
    model_override: Optional[str] = None,
    mode: Optional[str] = None,
    reason: Optional[str] = None,
    chain_id: Optional[str] = None,
    depth: Optional[int] = None,
) -> EmployeeRunResult:
    if employee_id not in EMPLOYEES:
        raise ValueError(f"未登録の社員ID: {employee_id}")

    resolved_mode = _infer_mode(sender, user_message, mode)
    run_reason = reason or f"{sender}: {user_message[:160]}"

    append_conversation_log(employee_id, {
        "kind": "in",
        "from": sender,
        "via": f"discord:{channel}" if channel else "cli",
        "text": user_message,
    })

    route = resolve_model_route(
        employee_id,
        resolved_mode,
        sender,
        user_message,
        run_reason,
        model_override,
    )

    circuit_reason = _circuit_skip_reason(resolved_mode, route.backend)
    if circuit_reason:
        append_conversation_log(employee_id, {
            "kind": "system_skip",
            "from": "employee_runner",
            "via": f"discord:{channel}" if channel else "cli",
            "text": circuit_reason,
        })
        write_usage_metric(
            employee_id=employee_id,
            mode=resolved_mode,
            reason=run_reason,
            skipped_reason=circuit_reason,
            model=route.model,
            effort=route.effort,
            route_tier=route.tier,
            route_reason=route.reason,
            route_escalated=route.escalated,
            fallback_model=route.fallback_model,
            chain_id=chain_id,
            depth=depth,
        )
        return EmployeeRunResult(
            ok=False,
            employee_id=employee_id,
            mode=resolved_mode,
            reason=run_reason,
            chain_id=chain_id,
            depth=depth,
            skipped_reason=circuit_reason,
        )

    ensure_claude_md(employee_id)
    prompt = _compose_prompt(employee_id, user_message, sender, resolved_mode, run_reason)
    prompt_chars = len(prompt) + _claude_md_chars(employee_id)
    use_resume = _should_use_resume(resolved_mode, sender, run_reason, user_message)
    used_resume = bool(load_session_state(employee_id).get("claude_session_id") and use_resume)

    try:
        # 同時実行制限（最大 2並列まで） - usage 制御
        async with _concurrency_semaphore:
            if route.backend == "codex":
                response = await run_codex(employee_id, prompt, route)
                used_resume = False
            else:
                response, used_resume = await run_claude_code(
                    employee_id, prompt, resolved_mode, use_resume, route
                )
    except Exception as e:
        log.exception(f"社員 {employee_id} 実行失敗")
        system_error = f"{type(e).__name__}: {e}"
        append_conversation_log(employee_id, {
            "kind": "system_error",
            "to": sender,
            "via": f"discord:{channel}" if channel else "cli",
            "text": system_error,
        })
        write_usage_metric(
            employee_id=employee_id,
            mode=resolved_mode,
            reason=run_reason,
            prompt_chars=prompt_chars,
            response_chars=0,
            used_resume=used_resume,
            model=route.model,
            effort=route.effort,
            route_tier=route.tier,
            route_reason=route.reason,
            route_escalated=route.escalated,
            fallback_model=route.fallback_model,
            chain_id=chain_id,
            depth=depth,
            skipped_reason="system_error",
        )
        await maybe_compress_log(employee_id)
        return EmployeeRunResult(
            ok=False,
            text="",
            employee_id=employee_id,
            mode=resolved_mode,
            reason=run_reason,
            prompt_chars=prompt_chars,
            used_resume=used_resume,
            model=route.model,
            effort=route.effort,
            route_tier=route.tier,
            route_reason=route.reason,
            route_escalated=route.escalated,
            fallback_model=route.fallback_model,
            chain_id=chain_id,
            depth=depth,
            skipped_reason="system_error",
            system_error=system_error,
        )

    response = response.strip()
    append_conversation_log(employee_id, {
        "kind": "out",
        "to": sender,
        "via": f"discord:{channel}" if channel else "cli",
        "text": response,
    })

    state = load_session_state(employee_id)
    state["last_active"] = now_jst_iso()
    state["last_mode"] = resolved_mode
    state["last_summary"] = response[:300]
    state["last_prompt_chars"] = prompt_chars
    state["last_response_chars"] = len(response)
    state["last_model"] = route.model
    state["last_effort"] = route.effort
    state["last_route_tier"] = route.tier
    state["last_route_reason"] = route.reason
    state["last_route_escalated"] = route.escalated
    state["total_messages"] = state.get("total_messages", 0) + 2
    save_session_state(employee_id, state)

    write_usage_metric(
        employee_id=employee_id,
        mode=resolved_mode,
        reason=run_reason,
        prompt_chars=prompt_chars,
        response_chars=len(response),
        used_resume=used_resume,
        model=route.model,
        effort=route.effort,
        route_tier=route.tier,
        route_reason=route.reason,
        route_escalated=route.escalated,
        fallback_model=route.fallback_model,
        chain_id=chain_id,
        depth=depth,
    )

    await maybe_compress_log(employee_id)
    return EmployeeRunResult(
        ok=True,
        text=response,
        employee_id=employee_id,
        mode=resolved_mode,
        reason=run_reason,
        prompt_chars=prompt_chars,
        response_chars=len(response),
        used_resume=used_resume,
        model=route.model,
        effort=route.effort,
        route_tier=route.tier,
        route_reason=route.reason,
        route_escalated=route.escalated,
        fallback_model=route.fallback_model,
        chain_id=chain_id,
        depth=depth,
    )


async def run_employee(
    employee_id: str,
    user_message: str,
    sender: str = "owner",
    channel: Optional[str] = None,
    model_override: Optional[str] = None,
    mode: Optional[str] = None,
    reason: Optional[str] = None,
    chain_id: Optional[str] = None,
    depth: Optional[int] = None,
) -> str:
    result = await run_employee_result(
        employee_id,
        user_message,
        sender=sender,
        channel=channel,
        model_override=model_override,
        mode=mode,
        reason=reason,
        chain_id=chain_id,
        depth=depth,
    )
    return result.text if result.ok else ""


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
