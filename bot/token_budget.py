"""社員 1 呼び出しあたりの注入 token 数を計測するユーティリティ。

token 数は Anthropic の文字数ヒューリスティックで推定:
  日本語混在テキスト: len(bytes(text, 'utf-8')) / 3 ≈ tokens

使い方:
    python -m bot.token_budget
"""
from __future__ import annotations

import math
from pathlib import Path

from .config import BASE_DIR, EMPLOYEES, employee_home
from .context_assembler import assemble_state_digest
from .employee_runner import build_employee_system_prompt

REPO_ROOT = BASE_DIR


def _estimate_tokens(text: str) -> int:
    """UTF-8バイト数 / 3 で token 数を推定（日本語混在テキスト向け）。"""
    return math.ceil(len(text.encode("utf-8")) / 3)


def measure_system_prompt(employee_id: str) -> dict:
    """1社員の system prompt (CLAUDE.md 相当) の token 数を計測。"""
    prompt = build_employee_system_prompt(employee_id)
    return {
        "employee_id": employee_id,
        "chars": len(prompt),
        "bytes": len(prompt.encode("utf-8")),
        "tokens_est": _estimate_tokens(prompt),
    }


def measure_state_digest(employee_id: str, mode: str = "routine") -> dict:
    """1社員の state_digest の token 数を計測。"""
    try:
        digest = assemble_state_digest(
            employee_id=employee_id,
            mode=mode,
            reason="token_budget_measurement",
            mentions=[],
            active_tasks=[],
            relevant_logs=[],
        )
    except Exception as e:
        digest = f"(error: {e})"
    return {
        "employee_id": employee_id,
        "mode": mode,
        "chars": len(digest),
        "bytes": len(digest.encode("utf-8")),
        "tokens_est": _estimate_tokens(digest),
    }


def measure_all() -> dict:
    """全社員の system_prompt + state_digest を計測してサマリを返す。"""
    results = []
    total_prompt_tokens = 0
    total_digest_tokens = 0

    for emp_id in EMPLOYEES:
        sp = measure_system_prompt(emp_id)
        sd = measure_state_digest(emp_id, mode="routine")
        total = sp["tokens_est"] + sd["tokens_est"]
        results.append({
            "employee_id": emp_id,
            "display": EMPLOYEES[emp_id].get("display", emp_id),
            "system_prompt_tokens": sp["tokens_est"],
            "state_digest_tokens": sd["tokens_est"],
            "total_per_call": total,
        })
        total_prompt_tokens += sp["tokens_est"]
        total_digest_tokens += sd["tokens_est"]

    return {
        "per_employee": results,
        "summary": {
            "total_system_prompt_tokens": total_prompt_tokens,
            "total_state_digest_tokens": total_digest_tokens,
            "total_all": total_prompt_tokens + total_digest_tokens,
            "avg_per_call": round((total_prompt_tokens + total_digest_tokens) / len(EMPLOYEES)),
        },
    }


def _fmt_row(r: dict) -> str:
    return (
        f"  {r['display']:<12} "
        f"prompt={r['system_prompt_tokens']:>4} "
        f"digest={r['state_digest_tokens']:>4} "
        f"total={r['total_per_call']:>4}"
    )


if __name__ == "__main__":
    print("=== Token Budget 計測 ===")
    data = measure_all()
    for r in data["per_employee"]:
        print(_fmt_row(r))
    s = data["summary"]
    print(f"\n合計 system_prompt: {s['total_system_prompt_tokens']} tokens")
    print(f"合計 state_digest : {s['total_state_digest_tokens']} tokens")
    print(f"全体合計          : {s['total_all']} tokens")
    print(f"1呼び出し平均     : {s['avg_per_call']} tokens")
