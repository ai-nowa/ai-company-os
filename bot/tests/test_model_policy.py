from __future__ import annotations

from bot.model_policy import needs_executive_model, resolve_model_route


def test_ceo_always_uses_codex_xhigh():
    route = resolve_model_route(
        "arima_reiji",
        mode="routine",
        sender="self_loop",
        user_message="今日の収益仮説を選ぶ",
        run_reason="self_loop",
    )

    assert route.backend == "codex"
    assert route.model == "gpt-5.5"
    assert route.effort == "xhigh"
    assert route.tier == "routine"


def test_revenue_routine_for_high_judgment_role_uses_high_sonnet():
    route = resolve_model_route(
        "kuroba_yuu",
        mode="routine",
        sender="self_loop",
        user_message="Revenue experiment の success_signal を更新する",
        run_reason="self_loop",
    )

    assert route.backend == "claude"
    assert route.model == "sonnet"
    assert route.effort == "high"
    assert route.tier == "business_routine"


def test_light_routine_for_viewer_rep_stays_medium_sonnet():
    route = resolve_model_route(
        "hinata_nagi",
        mode="routine",
        sender="self_loop",
        user_message="見学者向けの反応を見る",
        run_reason="self_loop",
    )

    assert route.model == "sonnet"
    assert route.effort == "medium"
    assert route.tier == "routine"


def test_executive_decision_uses_opus_xhigh():
    route = resolve_model_route(
        "saegusa_mio",
        mode="executive",
        sender="owner",
        user_message="価格と公開可否を決めてください",
        run_reason="owner decision",
    )

    assert route.model == "opus"
    assert route.effort == "xhigh"
    assert route.tier == "executive"
    assert route.fallback_model == "sonnet"


def test_crisis_uses_opus_max():
    route = resolve_model_route(
        "kagura_aoi",
        mode="routine",
        sender="owner",
        user_message="P0 security incident。流出可能性を監査して",
        run_reason="owner crisis",
    )

    assert route.model == "opus"
    assert route.effort == "max"
    assert route.tier == "crisis"


def test_executive_keyword_detection_includes_crisis():
    assert needs_executive_model("公開可否を判断")
    assert needs_executive_model("障害が起きた")
