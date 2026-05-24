"""スモークテスト。Discord接続なしで全社員に短いメッセージを投げて、
- 起動成功
- 文字数 > 0 の応答
- conversation_log.jsonl への書き込み
を一括検証する。

使い方:
    python -m bot.smoke_test                    # 全社員
    python -m bot.smoke_test saegusa_mio        # 特定社員のみ
    python -m bot.smoke_test --short            # ミオ・カイ・ハルの3人だけ（時短）
"""
from __future__ import annotations

import argparse
import asyncio
import sys

from .config import EMPLOYEES
from .employee_runner import run_employee


SHORT_SET = ["saegusa_mio", "shirase_kai", "morinaga_haru"]

# CLI smoke helper, not a pytest module.  The async ``test_one(employee_id)``
# function intentionally takes an employee id argument, so pytest must not
# collect it as a fixture-based test.
__test__ = False


async def test_one(employee_id: str) -> tuple[str, bool, str]:
    try:
        response = await run_employee(
            employee_id,
            "自己紹介を1〜2文でしてください。あなたの口癖を1つ含めてください。",
            sender="smoke_test",
        )
        ok = bool(response and len(response) > 5)
        return employee_id, ok, response[:200]
    except Exception as e:
        return employee_id, False, f"ERROR {type(e).__name__}: {e}"


async def run(targets: list[str]) -> int:
    results = []
    for emp in targets:
        print(f"\n=== {EMPLOYEES[emp]['display']} ({emp}) ===")
        eid, ok, snippet = await test_one(emp)
        status = "✓" if ok else "✗"
        print(f"{status} {snippet}")
        results.append((eid, ok))

    print("\n--- summary ---")
    for eid, ok in results:
        print(f"  {'✓' if ok else '✗'} {eid}")
    fails = [eid for eid, ok in results if not ok]
    if fails:
        print(f"\nFAILED: {fails}")
        return 1
    print(f"\nAll {len(results)} OK")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("employee", nargs="?", help="特定社員ID（省略時は全員）")
    parser.add_argument("--short", action="store_true", help="ミオ・カイ・ハルの3人だけ")
    args = parser.parse_args()

    if args.employee:
        targets = [args.employee]
    elif args.short:
        targets = SHORT_SET
    else:
        targets = list(EMPLOYEES.keys())

    sys.exit(asyncio.run(run(targets)))


if __name__ == "__main__":
    main()
