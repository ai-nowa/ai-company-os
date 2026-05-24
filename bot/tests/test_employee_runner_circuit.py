from __future__ import annotations

import json
import asyncio
from datetime import datetime, timedelta

from bot import employee_runner
from bot.config import JST
from bot.model_policy import ModelRoute


def _patch_circuit_config(monkeypatch):
    def fake_get(path: str, default=None):
        values = {
            "llm_circuit.enabled": True,
            "llm_circuit.claude_cooldown_minutes": 15,
            "llm_circuit.claude_failure_threshold": 2,
            "llm_circuit.claude_failure_window_minutes": 10,
        }
        return values.get(path, default)

    monkeypatch.setattr(employee_runner.dynamic_config, "get", fake_get)


def test_claude_circuit_does_not_skip_codex_backend(tmp_path, monkeypatch):
    _patch_circuit_config(monkeypatch)
    circuit_path = tmp_path / "circuit.json"
    now = datetime.now(JST)
    circuit_path.write_text(
        json.dumps({
            "open_until": (now + timedelta(hours=1)).isoformat(timespec="seconds"),
            "reason": "legacy claude circuit",
            "updated_at": now.isoformat(timespec="seconds"),
        }),
        encoding="utf-8",
    )
    monkeypatch.setattr(employee_runner, "CIRCUIT_STATE_PATH", circuit_path)

    assert employee_runner._circuit_skip_reason("routine", "codex") is None
    assert employee_runner._circuit_skip_reason("routine", "claude") is not None


def test_legacy_claude_circuit_uses_short_new_cooldown(tmp_path, monkeypatch):
    _patch_circuit_config(monkeypatch)
    circuit_path = tmp_path / "circuit.json"
    now = datetime.now(JST)
    circuit_path.write_text(
        json.dumps({
            "open_until": (now + timedelta(hours=1)).isoformat(timespec="seconds"),
            "reason": "legacy claude circuit",
            "updated_at": (now - timedelta(minutes=20)).isoformat(timespec="seconds"),
        }),
        encoding="utf-8",
    )
    monkeypatch.setattr(employee_runner, "CIRCUIT_STATE_PATH", circuit_path)

    assert employee_runner._circuit_skip_reason("routine", "claude") is None


def test_first_claude_failure_does_not_open_circuit(tmp_path, monkeypatch):
    _patch_circuit_config(monkeypatch)
    circuit_path = tmp_path / "circuit.json"
    monkeypatch.setattr(employee_runner, "CIRCUIT_STATE_PATH", circuit_path)

    opened = employee_runner._record_claude_failure_and_maybe_open("rc=1/no stderr")

    assert opened is False
    state = json.loads(circuit_path.read_text(encoding="utf-8"))
    assert "circuits" not in state or "claude" not in state["circuits"]


def test_empty_claude_success_opens_circuit_as_unavailable(tmp_path, monkeypatch):
    def fake_get(path: str, default=None):
        values = {
            "llm_circuit.enabled": True,
            "llm_circuit.claude_cooldown_minutes": 15,
            "llm_circuit.claude_failure_threshold": 1,
            "llm_circuit.claude_failure_window_minutes": 10,
        }
        return values.get(path, default)

    async def fake_exec(*args, **kwargs):
        return "", None, "", 0

    circuit_path = tmp_path / "circuit.json"
    monkeypatch.setattr(employee_runner.dynamic_config, "get", fake_get)
    monkeypatch.setattr(employee_runner, "CIRCUIT_STATE_PATH", circuit_path)
    monkeypatch.setattr(employee_runner, "_exec_claude", fake_exec)
    monkeypatch.setattr(employee_runner, "load_session_state", lambda employee_id: {})
    monkeypatch.setattr(employee_runner, "save_session_state", lambda employee_id, state: None)

    route = ModelRoute(
        backend="claude",
        model="opus",
        effort="xhigh",
        tier="executive",
        reason="test",
    )

    try:
        asyncio.run(employee_runner.run_claude_code("saegusa_mio", "test", "routine", False, route))
    except RuntimeError as exc:
        assert "no stderr" in str(exc)
    else:
        raise AssertionError("run_claude_code should fail on empty Claude output")

    state = json.loads(circuit_path.read_text(encoding="utf-8"))
    assert state["circuits"]["claude"]["reason"].endswith("(empty result)")
