from __future__ import annotations

from bot.employee_autonomy import build_self_prompt
from bot.employee_runner import _infer_mode
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


def test_self_loop_boilerplate_does_not_escalate_to_executive():
    prompt = build_self_prompt("asakura_noa")

    assert _infer_mode("self_loop", prompt, "routine") == "routine"

    route = resolve_model_route(
        "asakura_noa",
        mode="routine",
        sender="self_loop",
        user_message=prompt,
        run_reason="self_loop/startup: active taskあり, 新規成果物あり, 自分に関係するRevenue実験あり",
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
        user_message="短い反応を見る",
        run_reason="self_loop",
    )

    assert route.model == "sonnet"
    assert route.effort == "medium"
    assert route.tier == "routine"


def test_creative_routine_for_viewer_rep_uses_high_sonnet():
    route = resolve_model_route(
        "hinata_nagi",
        mode="routine",
        sender="self_loop",
        user_message="見学者向けの企画と改善案を考える",
        run_reason="self_loop",
    )

    assert route.model == "sonnet"
    assert route.effort == "high"
    assert route.tier == "creative_routine"


def test_risk_review_uses_opus_xhigh_before_crisis():
    route = resolve_model_route(
        "shirase_kai",
        mode="work",
        sender="owner",
        user_message="Cloudflare R2 の権限と webhook 自動化を実装する",
        run_reason="owner work",
    )

    assert route.model == "opus"
    assert route.effort == "xhigh"
    assert route.tier == "risk_review"


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
    assert needs_executive_model("APIキーと権限の扱いを確認")
