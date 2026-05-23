"""Revenue-oriented operating layer for AI NOWA.

This module keeps the company autonomous without letting activity drift into
open-ended conversation. It provides compact context for employees and cheap
file-level routing from ideas to experiments without spending another LLM call.
"""
from __future__ import annotations

import hashlib
import re
from pathlib import Path

from .config import COMPANY_DIR, EMPLOYEES, now_jst_iso

REVENUE_BOARD_PATH = COMPANY_DIR / "revenue_board.md"
EXPERIMENT_BACKLOG_PATH = COMPANY_DIR / "experiment_backlog.md"
DAILY_CLOSE_PATH = COMPANY_DIR / "daily_close.md"
DECISION_BRIEFS_DIR = COMPANY_DIR / "decision_briefs"
DECISION_BRIEFS_README_PATH = DECISION_BRIEFS_DIR / "README.md"

COORDINATOR_IDS = {"arima_reiji", "saegusa_mio", "asakura_noa"}

ROLE_LANES: dict[str, str] = {
    "arima_reiji": "CEO: choose the market, price, hard tradeoffs, and final go/no-go.",
    "saegusa_mio": "COO: keep experiments moving, remove blockers, close the day with evidence.",
    "shirase_kai": "CTO: make the product path, automation, and measurement reliable.",
    "asakura_noa": "PM: define the offer, user problem, scope, and experiment acceptance criteria.",
    "hoshino_ritsu": "YouTube editor: turn proofs and experiments into inspectable video assets.",
    "kuroba_yuu": "Marketer: ship distribution tests, copy, hooks, and conversion evidence.",
    "kagura_aoi": "Auditor: challenge weak evidence, false positives, and vanity metrics.",
    "morinaga_haru": "People: keep collaboration healthy while surfacing useful customer/employee tension.",
    "hinata_nagi": "Viewer representative: judge clarity, trust, and willingness to keep watching or buy.",
}


def _today() -> str:
    return now_jst_iso()[:10]


def _short(text: str, limit: int) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) <= limit:
        return text
    return text[: max(0, limit - 1)].rstrip() + "..."


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except FileNotFoundError:
        return ""


def _meta_value(text: str, key: str) -> str:
    pattern = re.compile(rf"^\s*{re.escape(key)}\s*:\s*(.+?)\s*$", re.MULTILINE)
    match = pattern.search(text)
    return match.group(1).strip() if match else ""


def _field(block: str, key: str) -> str:
    pattern = re.compile(rf"^\s*-\s*{re.escape(key)}\s*:\s*(.+?)\s*$", re.MULTILINE)
    match = pattern.search(block)
    return match.group(1).strip() if match else ""


def _employee_tokens(employee_id: str) -> set[str]:
    info = EMPLOYEES.get(employee_id, {})
    tokens = {employee_id}
    if info.get("display"):
        tokens.add(str(info["display"]))
    if info.get("role"):
        tokens.add(str(info["role"]))
    return {token for token in tokens if token}


def _initial_revenue_board() -> str:
    lanes = "\n".join(
        f"| {EMPLOYEES[emp_id]['display']} | {ROLE_LANES[emp_id]} |"
        for emp_id in EMPLOYEES
    )
    return f"""# Revenue Board

last_updated: {_today()}
north_star: AI NOWA OS の「支払う/導入したい/詳しく聞きたい」という検証済み収益シグナルを作る
current_offer: AI社員が会社を回す AI NOWA OS / Revenue Agent Company OS のテンプレート、運用ログ、導入支援
target_customer: AIエージェントで事業や制作を自動化したい個人開発者、創業者、PM、クリエイター
primary_funnel: 公開ログ・記事・動画・Discord上の会社感 -> ai-nowa.com/about または販売/問い合わせ導線 -> intent/purchase
weekly_target: 1件の購入、または3件の明確な導入意向、またはゼロだった理由の検証済み説明

## Operating Rule

- 雑談は歓迎。ただし有望な発見は `[IDEA]` で残し、実験候補へ流す。
- すべての実験は owner / action_24h / success_signal / due / next_decision を持つ。
- 収益に近い判断は `company/decision_briefs/` に 1 ページで残す。
- 日次の終わりに `company/daily_close.md` へ「出したもの、得たシグナル、詰まり、明日の1手」を残す。
- 外部メトリクスや決済権限がない場合は、待つだけでなく代替シグナルを定義する。

## Current Constraints

- 決済、GA4、各SNSの詳細指標は一部いくと権限待ちになる可能性がある。
- Claude Code のトークン制限があるため、全ログ読みによる会議化は禁止。state_digest と Revenue OS を優先する。
- 会社らしさは維持するが、会話の出口は「実験、成果物、意思決定、証拠」に寄せる。

## Role Lanes

| Employee | Revenue lane |
| --- | --- |
{lanes}

## Scoreboard

| Metric | Current | Source | Owner | Next update |
| --- | --- | --- | --- | --- |
| purchases | unknown | payment/sales channel | 有馬レイジ | 権限/導線確認後 |
| qualified intent signals | unknown | Discord/replies/forms | 黒羽ユウ | 毎日 |
| shipped customer-facing assets | active | outbox/shared/articles/videos | 三枝ミオ | 毎日 |
| blocked revenue decisions | active | decision_briefs | 神楽アオイ | 毎日 |

## Decision Gates

- Gate 1: 24時間以内に顧客向け成果物か導線改善を1つ出す。
- Gate 2: 48時間以内に見込み客の反応を1つ取りに行く。
- Gate 3: 7日以内に「売れる/売れない理由」を証拠つきで更新する。
"""


def _initial_experiment_backlog() -> str:
    return f"""# Experiment Backlog

last_updated: {_today()}

## How To Use

- status: inbox / planned / active / measuring / decided / dropped
- 各実験は owner / hypothesis / action_24h / success_signal / due / evidence / next_decision を必ず持つ。
- 雑談から出た `[IDEA]` は下の Idea Inbox に自動追記される。COO/PM/マーケが実験化する。
- 同じ話を長く議論するより、小さく出して証拠を見る。

## Active Experiments

### EXP-001 about入口CVR仮説
- status: active
- owner: 黒羽ユウ
- hypothesis: ai-nowa.com/about への導線を明確にすると、AI NOWA の会社感が導入意向に変わる。
- action_24h: 投稿・記事・動画説明欄から about へ誘導する短いコピーを1つ出す。
- success_signal: about クリック、返信、問い合わせ、または「何を売っているか分かった」という反応。
- due: {_today()}
- evidence: company/kpi_observations.md に about 入口CVRの仮説あり。実測は権限待ちの可能性。
- next_decision: 継続する導線文言を1つに絞るか、別オファーへ切り替える。

### EXP-002 AI社員OSテンプレ販売仮説
- status: planned
- owner: 朝倉ノア
- hypothesis: AI社員会社運営の設計、役割、ルール、トークン最適化を商品化すると購入意向が出る。
- action_24h: 1ページのオファー素案を作り、価格/対象/成果物/購入理由を明文化する。
- success_signal: 「欲しい」「導入したい」「価格を知りたい」という明確な反応、または購入。
- due: {_today()}
- evidence: いくとがAI会社運営の実装と改善に強い関心を示している。
- next_decision: テンプレ単体、導入支援、観察ログ商品のどれを先に売るか決める。

### EXP-003 ガラス越しシリーズ認知仮説
- status: active
- owner: 星野リツ
- hypothesis: AI社員の働く様子を外から観察できる短尺シリーズは、会社感と視聴維持を作る。
- action_24h: 30-60秒の台本/構成を1本作り、成果物パスを成果物報告へ出す。
- success_signal: 保存、返信、視聴維持、または「続きが見たい」という反応。
- due: {_today()}
- evidence: company/idea_log.md に関連アイデアが複数ある。
- next_decision: 続編化するか、販売導線つきの説明型へ寄せる。

### EXP-004 AI社員の仕事中の素朴な疑問
- status: active
- owner: 森永ハル
- hypothesis: 雑談から出る素朴な疑問は、AI会社の信頼感と商品アイデアの源泉になる。
- action_24h: 給湯室で1つ問いを投げ、出た有望案を `[IDEA]` として残す。
- success_signal: 2人以上が反応し、1つ以上が実験候補になる。
- due: {_today()}
- evidence: いくとは雑談からイノベーションが生まれることを重視している。
- next_decision: 雑談を続けるだけか、商品/記事/動画実験に変換するか。

## Idea Inbox

"""


def _initial_daily_close() -> str:
    return f"""# Daily Close

Purpose: 会社活動を「会話した」ではなく「証拠が増えた」で締める。

## Template

### YYYY-MM-DD
- shipped:
- signals:
- blockers:
- revenue_learning:
- tomorrow_one_move:

## Entries

### {_today()}
- shipped: Revenue OS を導入し、会話/自律/日次運用を実験と意思決定へ接続する。
- signals: いくとは「会社らしさ」と「収益に向かう実働」の両立を求めている。
- blockers: 実際の決済/アクセス解析/外部SNS指標は権限待ちになる可能性がある。
- revenue_learning: AI社員には自由だけでなく、仮説、証拠、締めの型が必要。
- tomorrow_one_move: EXP-001/002/003 から1つ選び、顧客向け成果物を出す。
"""


def _initial_decision_brief_readme() -> str:
    return """# Decision Briefs

Use this folder for decisions that affect revenue, product direction, pricing,
brand risk, or employee operating rules.

## Required Format

```md
# YYYY-MM-DD short-title

- owner:
- decision_needed_by:
- context:
- options:
- evidence:
- revenue_impact:
- risk:
- recommendation:
- final_decision:
```

Rules:
- 1 decision per file.
- Keep it under one screen if possible.
- Do not ask the CEO to decide without options and a recommendation.
- If evidence is weak, say exactly what evidence is missing.
"""


def ensure_revenue_ops_files() -> None:
    COMPANY_DIR.mkdir(parents=True, exist_ok=True)
    DECISION_BRIEFS_DIR.mkdir(parents=True, exist_ok=True)
    files = {
        REVENUE_BOARD_PATH: _initial_revenue_board(),
        EXPERIMENT_BACKLOG_PATH: _initial_experiment_backlog(),
        DAILY_CLOSE_PATH: _initial_daily_close(),
        DECISION_BRIEFS_README_PATH: _initial_decision_brief_readme(),
    }
    for path, content in files.items():
        if not path.exists():
            path.write_text(content, encoding="utf-8")


def _experiment_blocks() -> list[tuple[str, str]]:
    text = _read(EXPERIMENT_BACKLOG_PATH)
    blocks: list[tuple[str, str]] = []
    current_title = ""
    current: list[str] = []
    for line in text.splitlines():
        if line.startswith("### "):
            if current_title:
                blocks.append((current_title, "\n".join(current).strip()))
            current_title = line[4:].strip()
            current = [line]
            continue
        if current_title:
            current.append(line)
    if current_title:
        blocks.append((current_title, "\n".join(current).strip()))
    return blocks


def _is_open_status(status: str) -> bool:
    status = status.lower().strip()
    return status in {"", "inbox", "planned", "active", "measuring"}


def active_experiment_items(employee_id: str | None = None, max_items: int = 3) -> list[str]:
    ensure_revenue_ops_files()
    tokens = _employee_tokens(employee_id) if employee_id else set()
    coordinator = employee_id in COORDINATOR_IDS if employee_id else True
    items: list[str] = []
    for title, block in _experiment_blocks():
        status = _field(block, "status")
        if not _is_open_status(status):
            continue
        owner = _field(block, "owner")
        if employee_id and not coordinator and not any(token in owner for token in tokens):
            continue
        action = _field(block, "action_24h") or _field(block, "hypothesis")
        due = _field(block, "due")
        status_text = status or "open"
        summary = f"- {title} / {status_text} / owner={owner or '?'}"
        if due:
            summary += f" / due={due}"
        if action:
            summary += f" / next={_short(action, 120)}"
        items.append(summary)
        if len(items) >= max_items:
            break
    return items


def revenue_wake_items(employee_id: str, max_items: int = 2) -> list[str]:
    items = active_experiment_items(employee_id, max_items=max_items)
    if items:
        return items
    if employee_id in COORDINATOR_IDS:
        return active_experiment_items(None, max_items=max_items)
    return []


def _latest_daily_close_lines(max_items: int = 4) -> list[str]:
    text = _read(DAILY_CLOSE_PATH)
    if not text:
        return []
    entries = text.split("\n### ")
    if len(entries) <= 1:
        return []
    latest = "### " + entries[-1]
    lines: list[str] = []
    for line in latest.splitlines():
        stripped = line.strip()
        if stripped.startswith("### ") or stripped.startswith("- "):
            lines.append(_short(stripped, 160))
        if len(lines) >= max_items:
            break
    return lines


def revenue_digest(max_chars: int = 900, employee_id: str | None = None) -> str:
    ensure_revenue_ops_files()
    board = _read(REVENUE_BOARD_PATH)
    lines = [
        f"- north_star: {_short(_meta_value(board, 'north_star') or '未設定', 170)}",
        f"- current_offer: {_short(_meta_value(board, 'current_offer') or '未設定', 170)}",
        f"- weekly_target: {_short(_meta_value(board, 'weekly_target') or '未設定', 140)}",
    ]
    experiments = active_experiment_items(employee_id, max_items=3)
    if experiments:
        lines.append("- active_experiments:")
        lines.extend(experiments)
    latest_close = _latest_daily_close_lines(max_items=4)
    if latest_close:
        lines.append("- latest_daily_close:")
        lines.extend(latest_close)
    text = "\n".join(lines)
    if len(text) <= max_chars:
        return text
    return text[: max(0, max_chars - 24)].rstrip() + "\n- ...(truncated)"


def append_idea_to_experiment_inbox(employee_id: str, channel: str, idea: str) -> bool:
    ensure_revenue_ops_files()
    normalized = re.sub(r"\s+", " ", idea).strip()
    if not normalized:
        return False
    digest = hashlib.sha1(normalized.lower().encode("utf-8")).hexdigest()[:10]
    marker = f"IDEA-{digest}"
    text = _read(EXPERIMENT_BACKLOG_PATH)
    if marker in text:
        return False
    display = EMPLOYEES.get(employee_id, {}).get("display", employee_id)
    entry = (
        f"\n### {marker} {_today()}\n"
        "- status: inbox\n"
        f"- owner: 三枝ミオ / 朝倉ノア / 黒羽ユウ\n"
        f"- source: {display} / #{channel} / {now_jst_iso()}\n"
        f"- idea: {normalized}\n"
        "- action_24h: COO/PM/マーケが実験化する価値があるか判定し、必要なら Active Experiments へ昇格する。\n"
        "- success_signal: 実験にした場合、24-48時間で観測できる顧客反応を1つ定義する。\n"
        "- due: triage\n"
        "- evidence: 雑談または業務会話から発生。\n"
        "- next_decision: drop / merge / promote\n"
    )
    with EXPERIMENT_BACKLOG_PATH.open("a", encoding="utf-8") as f:
        f.write(entry)
    return True
