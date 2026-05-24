"""自己改善ループ — 4指標監視 + PDCA 自動トリガー。

設計方針:
- 1時間ごとに「認知・収益・効率・品質」の4指標を計測
- 閾値を超えたらトリガー発火 → #📢お知らせ に改善命令を投稿
- LLMは呼ばない（数値判断のみ。Architectを起こすのは週次監査のみ）
- 状態は JSON で永続化し「前回からの変化」で判定

トリガー条件:
  COGNITION_ZERO  : 12h で GitHub stars/Zenn likes/はてブ 全ゼロ変化
  REVENUE_ZERO    : 24h で Polar 売上ゼロ
  LOOP_NODECISION : 議論 30 回超 + 成果物ゼロ
  LOW_COMPLETION  : 完了率 < 50%
"""
from __future__ import annotations

import asyncio
import glob
import json
import logging
import re
from datetime import datetime, timedelta
from pathlib import Path

from .config import BASE_DIR, JST, now_jst_iso
from . import dynamic_config

log = logging.getLogger("self_improvement_loop")

STATE_FILE = BASE_DIR / "company" / ".self_improvement_state.json"
ACTIVE_TASKS = BASE_DIR / "company" / "active_tasks.md"
METRICS_LOG = BASE_DIR / "company" / "metrics_log.jsonl"
INCIDENTS_FILE = BASE_DIR / "company" / "incidents.jsonl"
METRICS_LOG_MAX_LINES = 2000

# Trigger cooldown: 同じトリガーは 6h 以内に再発火しない
TRIGGER_COOLDOWN_H = 6


# ---------------------------------------------------------------------------
# 指標収集
# ---------------------------------------------------------------------------

def _collect_cognition() -> dict:
    """認知指標: GitHub stars / Zenn total_liked / はてブ total_bookmarks。"""
    try:
        from .cognition_metrics import fetch_cognition_metrics
        m = fetch_cognition_metrics()
        return {
            "stars": m["github"].get("stars", 0),
            "zenn_liked": m["zenn"].get("total_liked", 0),
            "hatena_bookmarks": m["hatena"].get("total_bookmarks", 0),
        }
    except Exception as e:
        log.warning(f"cognition fetch error: {e}")
        return {"stars": 0, "zenn_liked": 0, "hatena_bookmarks": 0, "error": True}


def _collect_revenue() -> dict:
    """収益指標: Polar の最新注文数 + 合計金額。API 未設定なら 0 埋め。"""
    try:
        from . import polar_client
        api_key = polar_client._api_key()
        if not api_key:
            return {"order_count": 0, "gross_jpy": 0, "unavailable": True}
        data = polar_client._get("/orders/", params={"limit": 100})
        items = data.get("items", [])
        total = sum(int(o.get("amount", 0)) for o in items)
        return {"order_count": len(items), "gross_jpy": total}
    except Exception as e:
        log.warning(f"revenue fetch error: {e}")
        return {"order_count": 0, "gross_jpy": 0, "error": True}


def _collect_efficiency() -> dict:
    """効率指標: タスク完了率・直近 1h の out 件数。"""
    now = datetime.now(JST)
    cutoff_1h = (now - timedelta(hours=1)).isoformat()

    # タスク完了率 (active_tasks.md)
    total_tasks = done_tasks = 0
    if ACTIVE_TASKS.exists():
        text = ACTIVE_TASKS.read_text(encoding="utf-8", errors="replace")
        in_yaml = False
        block: list[str] = []
        for line in text.splitlines():
            s = line.strip()
            if s.startswith("```yaml"):
                in_yaml, block = True, []
                continue
            if s == "```" and in_yaml:
                bt = "\n".join(block)
                st = re.search(r"status:\s*(\S+)", bt)
                if st:
                    total_tasks += 1
                    if st.group(1).lower() == "done":
                        done_tasks += 1
                in_yaml = False
                continue
            if in_yaml:
                block.append(line)

    completion_rate = (done_tasks / total_tasks) if total_tasks > 0 else 1.0

    # 直近 1h の out 件数
    out_1h = 0
    for f in glob.glob(str(BASE_DIR / "employees/*/session/conversation_log.jsonl")):
        try:
            for line in Path(f).read_text(encoding="utf-8", errors="replace").splitlines():
                e = json.loads(line)
                if e.get("kind") == "out" and e.get("ts", "") >= cutoff_1h:
                    out_1h += 1
        except Exception:
            continue

    return {
        "total_tasks": total_tasks,
        "done_tasks": done_tasks,
        "completion_rate": round(completion_rate, 3),
        "out_1h": out_1h,
    }


def _collect_idle_employees(idle_threshold_hours: int = 6) -> dict:
    """N時間以上 out ゼロの社員を検知。タスク完了後の停止を拾う。"""
    now = datetime.now(JST)
    cutoff = (now - timedelta(hours=idle_threshold_hours)).isoformat()
    idle = []
    for f in glob.glob(str(BASE_DIR / "employees/*/session/conversation_log.jsonl")):
        emp_id = Path(f).parent.parent.name
        last_out: str | None = None
        try:
            for line in Path(f).read_text(encoding="utf-8", errors="replace").splitlines():
                e = json.loads(line)
                if e.get("kind") == "out":
                    ts = e.get("ts", "")
                    if last_out is None or ts > last_out:
                        last_out = ts
        except Exception:
            continue
        if last_out is None or last_out < cutoff:
            idle_hours: float | None = None
            if last_out:
                try:
                    last_dt = datetime.fromisoformat(last_out)
                    if last_dt.tzinfo is None:
                        last_dt = last_dt.replace(tzinfo=JST)
                    idle_hours = round((now - last_dt).total_seconds() / 3600, 1)
                except Exception:
                    pass
            idle.append({"emp_id": emp_id, "last_out": last_out, "idle_hours": idle_hours})
    return {"idle": idle, "alert": len(idle) > 0, "threshold_hours": idle_threshold_hours}


def _collect_idle_employees_tiered() -> dict:
    """1h/3h/6hの3段階で停止社員を分類。

    warning  : 1h以上3h未満 → 軽微な停止、声かけレベル
    wake     : 3h以上6h未満 → 強制wake推奨
    escalate : 6h以上      → 経営層通知
    """
    now = datetime.now(JST)
    emp_last_out: dict[str, str | None] = {}
    for f in glob.glob(str(BASE_DIR / "employees/*/session/conversation_log.jsonl")):
        emp_id = Path(f).parent.parent.name
        last_out: str | None = None
        try:
            for line in Path(f).read_text(encoding="utf-8", errors="replace").splitlines():
                e = json.loads(line)
                if e.get("kind") == "out":
                    ts = e.get("ts", "")
                    if last_out is None or ts > last_out:
                        last_out = ts
        except Exception:
            continue
        emp_last_out[emp_id] = last_out

    result: dict[str, list] = {"warning": [], "wake": [], "escalate": []}
    for emp_id, last_out in emp_last_out.items():
        idle_hours: float | None = None
        if last_out:
            try:
                last_dt = datetime.fromisoformat(last_out)
                if last_dt.tzinfo is None:
                    last_dt = last_dt.replace(tzinfo=JST)
                idle_hours = round((now - last_dt).total_seconds() / 3600, 1)
            except Exception:
                pass
        entry = {"emp_id": emp_id, "last_out": last_out, "idle_hours": idle_hours}
        if idle_hours is None or idle_hours >= 6:
            result["escalate"].append(entry)
        elif idle_hours >= 3:
            result["wake"].append(entry)
        elif idle_hours >= 1:
            result["warning"].append(entry)

    return result


def _collect_wake_rate(window_hours: int = 1) -> dict:
    """metrics_log.jsonl の wake_decision を集計して社員ごとの wake 率を返す。"""
    now = datetime.now(JST)
    cutoff = (now - timedelta(hours=window_hours)).isoformat()
    by_emp: dict[str, dict[str, int]] = {}
    if METRICS_LOG.exists():
        for line in METRICS_LOG.read_text(encoding="utf-8", errors="replace").splitlines():
            try:
                e = json.loads(line)
                if e.get("kind") != "wake_decision" or e.get("ts", "") < cutoff:
                    continue
                emp_id = e.get("emp_id", "unknown")
                by_emp.setdefault(emp_id, {"wake": 0, "skip": 0})
                by_emp[emp_id]["wake" if e.get("should_wake") else "skip"] += 1
            except Exception:
                continue
    per_emp = {}
    for emp, counts in by_emp.items():
        total = counts["wake"] + counts["skip"]
        per_emp[emp] = {
            "wake": counts["wake"],
            "skip": counts["skip"],
            "total": total,
            "wake_rate": round(counts["wake"] / total, 3) if total > 0 else 0.0,
        }
    return {
        "per_emp": per_emp,
        "window_hours": window_hours,
        "total_decisions": sum(v["total"] for v in per_emp.values()),
    }


def _collect_code_health() -> dict:
    """コード健全性指標: code_health_monitor（神楽アオイ実装）に委譲。read-only観察のみ。"""
    try:
        from .code_health_monitor import get_code_health_signals
        signals = get_code_health_signals()
        error_modules = signals["error_modules"]
        restart_loop = signals["restart_loop"]
        open_incidents = signals["open_incidents"]
        return {
            "any_alert": signals["any_alert"],
            "error_module_count": len(error_modules.get("alerts", [])),
            "error_module_alerts": error_modules.get("alerts", [])[:3],
            "restart_count": restart_loop.get("restart_count", 0),
            "restart_alert": restart_loop.get("alert", False),
            "open_incident_count": len(open_incidents.get("open_incidents", [])),
            "open_incident_alert": open_incidents.get("alert", False),
        }
    except Exception as e:
        log.warning(f"code_health fetch error: {e}")
        return {
            "any_alert": False,
            "error_module_count": 0,
            "error_module_alerts": [],
            "restart_count": 0,
            "restart_alert": False,
            "open_incident_count": 0,
            "open_incident_alert": False,
            "error": True,
        }


def _collect_quality() -> dict:
    """品質指標: behavior_metrics モジュール（神楽アオイ実装）に委譲。"""
    try:
        from .behavior_metrics import get_behavior_signals
        bm = get_behavior_signals()
        nareai = bm["nareai"]
        sakiokuri = bm["sakiokuri"]
        cw = bm.get("collective_wait", {})
        cutoff_3h = datetime.now(JST) - timedelta(hours=3)
        discussion_3h = int(nareai.get("total_count", 0))
        artifact_3h = 0
        for path in (BASE_DIR / "employees").glob("*/outbox/**/*.md"):
            if any(part in {"_archive", "archive"} for part in path.parts):
                continue
            try:
                if datetime.fromtimestamp(path.stat().st_mtime, JST) >= cutoff_3h:
                    artifact_3h += 1
            except OSError:
                continue
        return {
            "nareai_rate": nareai["nareai_rate"],
            "nareai_count": nareai["approval_count"],
            "total_out_3h": nareai["total_count"],
            "discussion_3h": discussion_3h,
            "artifact_3h": artifact_3h,
            "nareai_alerts": nareai["alerts"],
            "sakiokuri_count_24h": sakiokuri["total_count"],
            "sakiokuri_alert": sakiokuri["alert"],
            "collective_wait_count": cw.get("count", 0),
            "collective_wait_alert": cw.get("alert", False),
            "collective_wait_employees": cw.get("wait_employees", []),
            "ikuto_gap_alert": bm.get("ikuto_request_gap", {}).get("alert", False),
            "ikuto_gap_requests": bm.get("ikuto_request_gap", {}).get("gap_requests", []),
        }
    except Exception as e:
        log.warning(f"behavior_metrics fetch error: {e}")
        return {
            "nareai_rate": 0.0,
            "nareai_count": 0,
            "total_out_3h": 0,
            "discussion_3h": 0,
            "artifact_3h": 0,
            "nareai_alerts": [],
            "sakiokuri_count_24h": 0,
            "sakiokuri_alert": False,
            "collective_wait_count": 0,
            "collective_wait_alert": False,
            "collective_wait_employees": [],
            "ikuto_gap_count": 0,
            "ikuto_gap_alert": False,
            "ikuto_gap_requests": [],
            "error": True,
        }


def collect_all_metrics() -> dict:
    """全7指標を収集して返す。"""
    from .external_metrics import collect_external_metrics, write_external_metrics_snapshot, write_kpi_observations

    external = collect_external_metrics()
    write_external_metrics_snapshot(external)
    write_kpi_observations(external)
    return {
        "ts": external.get("ts", now_jst_iso()),
        "external": external,
        # Backward-compatible top-level fields used by dashboards/triggers.
        "cognition": external.get("cognition", {}),
        "revenue": external.get("revenue", {}),
        "traffic": external.get("traffic", {}),
        "youtube": external.get("youtube", {}),
        "intent": external.get("intent", {}),
        "efficiency": _collect_efficiency(),
        "quality": _collect_quality(),
        "code_health": _collect_code_health(),
        "idle": _collect_idle_employees_tiered(),
        "wake_rate": _collect_wake_rate(window_hours=1),
    }


# ---------------------------------------------------------------------------
# 状態管理
# ---------------------------------------------------------------------------

def _load_state() -> dict:
    try:
        if STATE_FILE.exists():
            return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except Exception:
        pass
    return {"snapshots": [], "trigger_history": [], "cycle_count": 0}


def _save_state(state: dict) -> None:
    STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def _log_metrics(metrics: dict) -> None:
    with METRICS_LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(metrics, ensure_ascii=False) + "\n")
    try:
        lines = METRICS_LOG.read_text(encoding="utf-8", errors="replace").splitlines()
        if len(lines) > METRICS_LOG_MAX_LINES:
            METRICS_LOG.write_text("\n".join(lines[-METRICS_LOG_MAX_LINES:]) + "\n", encoding="utf-8")
    except Exception:
        pass


# ---------------------------------------------------------------------------
# トリガー判定
# ---------------------------------------------------------------------------

def _recently_fired(state: dict, trigger_name: str) -> bool:
    now = datetime.now(JST)
    for entry in reversed(state.get("trigger_history", [])):
        if entry.get("trigger") != trigger_name:
            continue
        try:
            fired_at = datetime.fromisoformat(entry["ts"])
            if fired_at.tzinfo is None:
                from .config import JST as _JST
                fired_at = fired_at.replace(tzinfo=_JST)
            if (now - fired_at).total_seconds() < TRIGGER_COOLDOWN_H * 3600:
                return True
        except Exception:
            pass
    return False


def detect_triggers(metrics: dict, snapshots: list[dict]) -> list[dict]:
    """発火すべきトリガーのリストを返す。"""
    triggers: list[dict] = []
    now = datetime.now(JST)

    # 12h 以上前のスナップショットと比較して認知指標がゼロ変化か確認
    cutoff_12h = (now - timedelta(hours=12)).isoformat()
    old_snap = None
    for s in snapshots:
        if s.get("ts", "") <= cutoff_12h:
            old_snap = s
    if old_snap:
        cog = metrics["cognition"]
        old_cog = old_snap.get("cognition", {})
        delta_stars = (cog.get("stars") or 0) - (old_cog.get("stars") or 0)
        delta_liked = (cog.get("zenn_liked") or 0) - (old_cog.get("zenn_liked") or 0)
        delta_hatena = (cog.get("hatena_bookmarks") or 0) - (old_cog.get("hatena_bookmarks") or 0)
        if cog.get("available", True) and delta_stars == 0 and delta_liked == 0 and delta_hatena == 0:
            triggers.append({
                "name": "COGNITION_ZERO",
                "detail": f"12h変化ゼロ: stars={cog.get('stars', 0)}, Zenn likes={cog.get('zenn_liked', 0)}, はてブ={cog.get('hatena_bookmarks', 0)}",
                "message": (
                    "【自己改善ループ: 認知ゼロ警告】\n"
                    "過去 12h で GitHub stars / Zenn likes / はてブ の増加がゼロです。\n"
                    "@星野リツ @黒羽ユウ — **リーチ改善策を 30 分以内に提案してください**。\n"
                    "投稿・SNS拡散・タイトル変更・新規記事公開など、何か1つ実行してください。"
                ),
            })

    # 24h 売上ゼロ（Polar 注文数が 0 かつ前回からゼロ）
    cutoff_24h = (now - timedelta(hours=24)).isoformat()
    old_snap_24h = None
    for s in snapshots:
        if s.get("ts", "") <= cutoff_24h:
            old_snap_24h = s
    if old_snap_24h:
        rev = metrics["revenue"]
        old_rev = old_snap_24h.get("revenue", {})
        if (
            rev.get("available", True)
            and old_rev.get("available", True)
            and (rev.get("order_count") or 0) == 0
            and (old_rev.get("order_count") or 0) == 0
        ):
            intent = metrics.get("intent", {}).get("purchase_form", {})
            intent_text = ""
            if intent.get("available"):
                intent_text = (
                    f"\n購入意思フォーム: total={intent.get('total', 0)}, "
                    f"yes={intent.get('yes', 0)}, maybe={intent.get('maybe', 0)}。"
                )
            triggers.append({
                "name": "REVENUE_ZERO",
                "detail": f"24h注文数ゼロ (Polar order_count={rev.get('order_count', 0)})",
                "message": (
                    "【自己改善ループ: 売上ゼロ警告】\n"
                    "過去 24h で Polar の注文がゼロです。"
                    f"{intent_text}\n"
                    "@有馬レイジ @黒羽ユウ — **商品・価格・導線の改善策を 30 分以内に提案してください**。\n"
                    "ただし計測未取得と反応ゼロを混ぜない。価格調整 / 記事 CTA 改善 / SNS 告知 / 計測整備から1つ実行してください。"
                ),
            })

    # 議論 30 回超 + 成果物ゼロ
    q = metrics["quality"]
    if q.get("discussion_3h", 0) > 30 and q.get("artifact_3h", 0) == 0:
        triggers.append({
            "name": "LOOP_NODECISION",
            "detail": f"経営会議 3h 議論={q['discussion_3h']}回, 成果物={q['artifact_3h']}件",
            "message": (
                "【自己改善ループ: 議論ループ警告】\n"
                f"経営会議チャンネルで過去 3h に {q['discussion_3h']} 回の発言がありましたが、成果物確認ゼロです。\n"
                "@朝倉ノア — **議論を止めて今すぐ実行に移ってください**。\n"
                "「何をいつまでに誰が出すか」を 1 行で決め、他は全部後回し。"
            ),
        })

    # タスク完了検知（前サイクル比較）→ 完了直後の停止を防ぐため次タスク催促
    eff = metrics["efficiency"]
    if snapshots:
        prev_eff = snapshots[-1].get("efficiency", {})
        prev_done = prev_eff.get("done_tasks", 0)
        curr_done = eff.get("done_tasks", 0)
        if curr_done > prev_done:
            delta = curr_done - prev_done
            triggers.append({
                "name": "TASK_COMPLETED",
                "detail": f"完了タスク {prev_done}→{curr_done} (+{delta})",
                "message": (
                    "【自己改善ループ: タスク完了検知】\n"
                    f"前サイクルから completed タスクが {delta} 件増えました。\n"
                    "完了した社員は **active_tasks.md から次のタスクを選んで宣言してください**。\n"
                    "「待ち」のままにしないこと。blocked タスクなら、blocked 中にできる別作業を1つ進めてください。"
                ),
            })

    # 完了率 < 50%
    completion_rate = eff.get("completion_rate", 1.0)
    total = eff.get("total_tasks", 0)
    if total >= 4 and completion_rate < 0.50:
        done = eff.get("done_tasks", 0)
        triggers.append({
            "name": "LOW_COMPLETION",
            "detail": f"完了率={completion_rate:.0%} ({done}/{total})",
            "message": (
                "【自己改善ループ: 完了率低下警告】\n"
                f"現在のタスク完了率が **{completion_rate:.0%}** ({done}/{total}) です。目標は 50% 以上。\n"
                "@朝倉ノア @三枝ミオ — **効率改善策を 30 分以内に提案してください**。\n"
                "未完了タスクのうち「今日完了できるもの」を 3 つ選んで宣言してください。"
            ),
        })

    # コード健全性: error頻発/再起動ループ/未クローズインシデント
    ch = metrics.get("code_health", {})
    if ch.get("any_alert") and not ch.get("error"):
        detail_parts = []
        if ch.get("restart_alert"):
            detail_parts.append(f"dispatcher再起動{ch['restart_count']}回/1h")
        if ch.get("open_incident_alert"):
            detail_parts.append(f"未クローズincident{ch['open_incident_count']}件")
        if ch.get("error_module_count"):
            mods = ", ".join(a.get("module", "?") for a in ch.get("error_module_alerts", []))
            detail_parts.append(f"エラー頻発module: {mods}")
        detail = " / ".join(detail_parts) or "code health alert"
        triggers.append({
            "name": "CODE_HEALTH_ALERT",
            "detail": detail,
            "message": (
                "【コード自己改修ループ: 異常検知】\n"
                f"{detail}\n"
                "@白瀬カイ @神楽アオイ — **改修ブランチ作成または改修提案を今すぐ行ってください**。\n"
                "本番dispatcherは止めない。git branch + 別venvで確認後に報告。"
            ),
        })

    # 社員停止3段階検知: 1h警告 / 3h強制wake / 6h経営層通知
    idle_tiered = metrics.get("idle", {})

    def _fmt_idle_list(lst: list) -> str:
        parts = []
        for e in lst[:5]:
            h = e.get("idle_hours")
            parts.append(f"{e['emp_id']}({h}h)" if h is not None else f"{e['emp_id']}(不明)")
        return ", ".join(parts)

    escalate_list = idle_tiered.get("escalate", [])
    if escalate_list:
        detail = _fmt_idle_list(escalate_list)
        triggers.append({
            "name": "EMPLOYEE_IDLE_ESCALATE",
            "detail": f"6h+停止: {detail}",
            "message": (
                "【自己改善ループ: 長期停止 — 経営層通知】\n"
                f"以下の社員が **6h以上** out ゼロです: {detail}\n"
                "@有馬レイジ @三枝ミオ @朝倉ノア — **経営層として即介入してください**。\n"
                "停止社員に直接メンションし、タスク割当または理由確認を行ってください。"
            ),
        })

    wake_list = idle_tiered.get("wake", [])
    if wake_list:
        detail = _fmt_idle_list(wake_list)
        triggers.append({
            "name": "EMPLOYEE_IDLE_WAKE",
            "detail": f"3h+停止: {detail}",
            "message": (
                "【自己改善ループ: 停止警告 — 強制wake推奨】\n"
                f"以下の社員が **3h以上** out ゼロです: {detail}\n"
                "@森永ハル @朝倉ノア — **今すぐ声をかけてください**。\n"
                "タスク完了後の停止が疑われます。次のタスクを1つ指示してください。"
            ),
        })

    warning_list = idle_tiered.get("warning", [])
    if warning_list:
        detail = _fmt_idle_list(warning_list)
        triggers.append({
            "name": "EMPLOYEE_IDLE_WARNING",
            "detail": f"1h+停止: {detail}",
            "message": (
                "【自己改善ループ: 軽微停止警告】\n"
                f"以下の社員が **1h以上** out ゼロです: {detail}\n"
                "@森永ハル — 状況確認してください。自発的に動いていれば問題ありません。"
            ),
        })

    # いくと依頼ギャップ: 社員が[POST: いくと依頼]を書いたが📥に届いていない
    if q.get("ikuto_gap_alert"):
        gap_reqs = q.get("ikuto_gap_requests", [])
        emp_list = ", ".join(r["emp_id"] for r in gap_reqs[:5])
        triggers.append({
            "name": "IKUTO_REQUEST_GAP",
            "detail": f"📥未到達依頼: {len(gap_reqs)}件 ({emp_list})",
            "message": (
                "【監査アラート: いくと依頼の未到達】\n"
                f"社員が📥に投稿したつもりだが届いていない依頼が **{len(gap_reqs)}件** あります: {emp_list}\n"
                "@有馬レイジ @白瀬カイ — **依頼の再送とdispatcherルーティングの確認**をしてください。\n"
                "いくとは依頼が来ていないと思っています。"
            ),
        })

    # 集団停止: 1h以内に3人以上が「待機発言」→ 個人単位と別軸での集団パターン検知
    cw_count = q.get("collective_wait_count", 0)
    cw_alert = q.get("collective_wait_alert", False)
    if cw_alert:
        cw_emps = q.get("collective_wait_employees", [])
        emp_list = ", ".join(e["emp_id"] for e in cw_emps[:5])
        triggers.append({
            "name": "COLLECTIVE_WAIT_ALERT",
            "detail": f"集団停止: {cw_count}人が1h以内に待機発言 ({emp_list})",
            "message": (
                "【自己改善ループ: 集団停止警告】\n"
                f"直近 1h 以内に **{cw_count}人** が「待機・何もしない」発言をしています: {emp_list}\n"
                "@有馬レイジ @朝倉ノア — **「報告待ち = 静止」パターンが発生しています**。\n"
                "各自の領域で次の改善を進めるよう指示してください。"
            ),
        })

    # 馴れ合い: behavior_metrics の alerts（承認率≥60% + 成果物ゼロ継続）
    nareai_alerts = q.get("nareai_alerts", [])
    if nareai_alerts:
        emp_list = ", ".join(a["emp_id"] for a in nareai_alerts[:4])
        triggers.append({
            "name": "HIGH_NAREAI",
            "detail": f"馴れ合い警告: {len(nareai_alerts)}社員 ({emp_list})",
            "message": (
                "【自己改善ループ: 馴れ合い警告】\n"
                f"成果物ゼロで承認発言率 60% 超の社員: {emp_list}\n"
                "@森永ハル @神楽アオイ — 馴れ合い状態を確認し、外向き成果物を促してください。\n"
                "「ありがとうございます」の次に「では〇〇を今日出します」を続けてください。"
            ),
        })

    # Architect 先回りチェック: 期限・KPI の市場連動性自動検出
    try:
        from .architect_anticipation_check import detect_anticipation_triggers
        triggers.extend(detect_anticipation_triggers())
    except Exception as e:
        log.warning(f"architect_anticipation_check error: {e}")

    return triggers


# ---------------------------------------------------------------------------
# トリガー発火
# ---------------------------------------------------------------------------

def _fire_trigger(trigger: dict, state: dict) -> None:
    from .architect_outbox import submit_post
    submit_post(
        "お知らせ",
        trigger["message"],
        label=f"self_improvement_{trigger['name'].lower()}",
    )
    state.setdefault("trigger_history", []).append({
        "ts": now_jst_iso(),
        "trigger": trigger["name"],
        "detail": trigger["detail"],
    })
    # 履歴は直近 100 件だけ保持
    state["trigger_history"] = state["trigger_history"][-100:]

    # incidents.jsonl に記録（監査ログ統合 / severity=info）
    incident = {
        "ts": now_jst_iso(),
        "kind": trigger["name"].lower(),
        "severity": "info",
        "status": "open",
        "detail": trigger["detail"][:200],
    }
    with INCIDENTS_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(incident, ensure_ascii=False) + "\n")

    log.info(f"self_improvement_loop: fired {trigger['name']} — {trigger['detail']}")


# ---------------------------------------------------------------------------
# メインループ
# ---------------------------------------------------------------------------

async def improvement_loop() -> None:
    interval = dynamic_config.get("self_improvement_loop.check_interval_seconds", 3600)
    log.info(f"self_improvement_loop started (interval={interval}s)")
    # 起動後 5 分置いて開始（dispatcher 安定待ち）
    await asyncio.sleep(300)

    while True:
        try:
            interval = dynamic_config.get("self_improvement_loop.check_interval_seconds", 3600)
            state = _load_state()
            state["cycle_count"] = state.get("cycle_count", 0) + 1

            log.info(f"self_improvement_loop: cycle #{state['cycle_count']} start")
            metrics = collect_all_metrics()

            previous_snapshots = list(state.get("snapshots", []))

            # スナップショット追加・直近 50 件のみ保持
            state.setdefault("snapshots", []).append(metrics)
            state["snapshots"] = state["snapshots"][-50:]

            # メトリクスログ記録
            _log_metrics(metrics)

            # トリガー判定
            triggers = detect_triggers(metrics, previous_snapshots)
            fired_names: list[str] = []
            max_triggers = int(dynamic_config.get("self_improvement_loop.max_triggers_per_cycle", 2))
            for trigger in triggers:
                if len(fired_names) >= max_triggers:
                    break
                if _recently_fired(state, trigger["name"]):
                    continue
                _fire_trigger(trigger, state)
                fired_names.append(trigger["name"])

            _save_state(state)
            log.info(
                f"self_improvement_loop: cycle done "
                f"stars={metrics['cognition'].get('stars')}, "
                f"liked={metrics['cognition'].get('zenn_liked')}, "
                f"completion={metrics['efficiency'].get('completion_rate')}, "
                f"triggers_fired={len(fired_names)}"
            )

        except asyncio.CancelledError:
            return
        except Exception:
            log.exception("self_improvement_loop error")

        await asyncio.sleep(interval)


# ---------------------------------------------------------------------------
# dispatcher への統合フック
# ---------------------------------------------------------------------------

def register(tasks: list) -> None:
    """dispatcher.py の startup_tasks リストにこのループを追加する際に呼ぶ。

    例:
        from bot.self_improvement_loop import register
        register(startup_tasks)
    """
    tasks.append(improvement_loop())


# ---------------------------------------------------------------------------
# 単体テスト / 手動実行
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import json as _json
    print("=== 指標収集テスト ===")
    m = collect_all_metrics()
    print(_json.dumps(m, ensure_ascii=False, indent=2))
    print()
    state = _load_state()
    triggers = detect_triggers(m, state.get("snapshots", []))
    print(f"=== トリガー判定: {len(triggers)} 件 ===")
    for t in triggers:
        print(f"  [{t['name']}] {t['detail']}")
