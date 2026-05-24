from __future__ import annotations

from bot.architect import _compose_prompt, _trim_response
from bot.architect_policy import architect_mode_settings, should_auto_architect_respond


def test_auto_architect_mode_is_fresh_and_capped():
    settings = architect_mode_settings("auto")

    assert settings.model == "claude-opus-4-7"
    assert settings.use_resume is False
    assert settings.max_output_tokens <= 1200
    assert settings.max_response_chars <= 1200


def test_manual_architect_keeps_resume_for_founder_consultation():
    settings = architect_mode_settings("manual")

    assert settings.use_resume is True
    assert settings.effort == "xhigh"


def test_noncritical_architect_mention_from_regular_employee_is_blocked():
    decision = should_auto_architect_respond(
        "@設計者 これ、雰囲気としてどう見えますか？",
        "hoshino_ritsu",
    )

    assert decision.allowed is False
    assert decision.reason == "noncritical_employee_architect_mention"


def test_critical_architect_mention_from_any_employee_is_allowed():
    decision = should_auto_architect_respond(
        "@設計者 本番deploy後にAPIキー流出の可能性があります",
        "hoshino_ritsu",
    )

    assert decision.allowed is True
    assert decision.reason == "critical_keyword"


def test_allowed_leadership_employee_can_auto_consult_architect():
    decision = should_auto_architect_respond(
        "@設計者 この会社構造の設計レビューをください",
        "saegusa_mio",
    )

    assert decision.allowed is True
    assert decision.reason == "allowed_employee"


def test_auto_prompt_forces_auditor_shape_not_boss_shape():
    settings = architect_mode_settings("auto")
    prompt = _compose_prompt(
        "@設計者 価格判断をしてください",
        "社員（三枝ミオ）",
        "経営会議",
        settings,
    )

    assert "社員の判断を奪わず" in prompt
    assert "差し戻し" in prompt
    assert "問題:" in prompt
    assert "次の1手:" in prompt


def test_architect_response_trim_has_hard_cap():
    text = "a" * 2000
    trimmed = _trim_response(text, 1200)

    assert len(trimmed) <= 1200
    assert "上限" in trimmed
