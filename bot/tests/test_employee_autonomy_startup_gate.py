from __future__ import annotations

import asyncio

from bot import employee_autonomy


def _patch_startup_config(monkeypatch):
    def fake_get(path: str, default=None):
        values = {
            "employee_autonomy.startup_max_llm_calls": 2,
            "employee_autonomy.startup_nonpriority_min_score": 7,
            "employee_autonomy.startup_priority_employee_ids": ["saegusa_mio", "arima_reiji"],
        }
        return values.get(path, default)

    monkeypatch.setattr(employee_autonomy.dynamic_config, "get", fake_get)
    monkeypatch.setattr(employee_autonomy, "_startup_llm_calls", 0)
    monkeypatch.setattr(employee_autonomy, "_startup_gate_lock", asyncio.Lock())


def test_startup_gate_skips_low_score_nonpriority(monkeypatch):
    _patch_startup_config(monkeypatch)

    reason = asyncio.run(employee_autonomy._startup_skip_reason("hoshino_ritsu", 3, "startup"))

    assert reason == "startup_nonpriority_score=3<min=7"


def test_startup_gate_allows_budget_then_skips(monkeypatch):
    _patch_startup_config(monkeypatch)

    first = asyncio.run(employee_autonomy._startup_skip_reason("saegusa_mio", 3, "startup"))
    second = asyncio.run(employee_autonomy._startup_skip_reason("arima_reiji", 3, "startup"))
    third = asyncio.run(employee_autonomy._startup_skip_reason("shirase_kai", 8, "startup"))

    assert first is None
    assert second is None
    assert third == "startup_budget_exhausted:2"
