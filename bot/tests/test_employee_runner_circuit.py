from __future__ import annotations

import json
from datetime import datetime, timedelta

from bot import employee_runner
from bot.config import JST


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
