"""9人の日常を毎日1本の物語草稿に変換する。

和佐ノウハウ設計原則:
- 素人性の保護: 失敗・差し戻し・摩擦を消さず、むしろ主役に置く
- キャラクター第一: 「誰が誰に何を言ったか」が物語の核
- 問題解決ベースNG: 機能完成より摩擦・感情・和解を出力する

使用方法:
    python -m bot.storyteller            # 今日分を生成
    python -m bot.storyteller --date 2026-05-22
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent / ".env")

JST = timezone(timedelta(hours=9))
REPO_ROOT = Path(__file__).parent.parent
INCIDENTS_PATH = REPO_ROOT / "company" / "incidents.jsonl"
DISCORD_LOG_PATH = REPO_ROOT / "company" / "discord_log.jsonl"
STORIES_DIR = REPO_ROOT / "company" / "stories"
EMPLOYEES_DIR = REPO_ROOT / "employees"
STORY_USED_INCIDENTS_PATH = REPO_ROOT / "company" / ".story_incidents_used.jsonl"

EMPLOYEE_DISPLAY = {
    "arima_reiji": "有馬レイジ",
    "saegusa_mio": "三枝ミオ",
    "shirase_kai": "白瀬カイ",
    "asakura_noa": "朝倉ノア",
    "hoshino_ritsu": "星野リツ",
    "kuroba_yuu": "黒羽ユウ",
    "kagura_aoi": "神楽アオイ",
    "morinaga_haru": "森永ハル",
    "hinata_nagi": "日向ナギ",
}


@dataclass
class DramaMoment:
    """物語に使える「摩擦・失敗・和解」の1シーン。"""
    ts: str
    actor: str           # 主体（employee_id）
    target: str          # 受け手（employee_id or ""）
    kind: str            # clash / failure / recovery / praise / escalation
    raw: str             # 生テキスト（消さない、素人性の保護）
    emotion_hint: str = ""   # 怒り・戸惑い・安堵など（あれば）


@dataclass
class StoryContext:
    """LLMに渡す物語生成コンテキスト。"""
    target_date: str
    protagonist: str          # 今日の主役（最も摩擦・挑戦が多かった社員）
    moments: list[DramaMoment] = field(default_factory=list)
    outbox_fragments: list[str] = field(default_factory=list)   # 今日の成果物タイトル断片
    arc_hint: str = ""         # 序破急のどこに重心を置くか
    atmosphere: str = ""       # 今日の空気感（Discord投稿用・一言）
    drama_framing: str = "challenger"
    # "challenger" — 主役は「問題を起こした人」ではなく「困難に挑んだ人」として描く
    # "neutral"    — 事実のみ並べる（編集者が後からトーンを決める用途）
    # "observer"   — 第三者視点、感情評価なし（アーカイブ・議事録用途）


# ---------- incidents 重複防止 ----------

def _load_used_incident_ids() -> set[str]:
    """既にストーリー化済みの incident id を返す。"""
    if not STORY_USED_INCIDENTS_PATH.exists():
        return set()
    used: set[str] = set()
    for line in STORY_USED_INCIDENTS_PATH.read_text(encoding="utf-8").splitlines():
        try:
            entry = json.loads(line)
            used.add(entry["incident_id"])
        except Exception:
            continue
    return used


def _mark_incidents_used(incidents: list[dict], story_date: date) -> None:
    """使用済み incident id を記録する。id フィールドがなければ ts で代替。"""
    STORY_USED_INCIDENTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    ts_now = datetime.now(JST).isoformat()
    with STORY_USED_INCIDENTS_PATH.open("a", encoding="utf-8") as f:
        for ev in incidents:
            inc_id = ev.get("id") or ev.get("ts", "")
            if not inc_id:
                continue
            entry = {
                "ts": ts_now,
                "story_date": story_date.isoformat(),
                "incident_id": inc_id,
            }
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")


# ---------- 入力収集 ----------

def collect_incidents(target_date: date) -> list[dict]:
    """incidents.jsonlから対象日の摩擦イベントを収集する。"""
    if not INCIDENTS_PATH.exists():
        return []
    result = []
    for line in INCIDENTS_PATH.read_text(encoding="utf-8").splitlines():
        try:
            ev = json.loads(line)
            ts = datetime.fromisoformat(ev["ts"])
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=JST)
            if ts.date() == target_date:
                result.append(ev)
        except Exception:
            continue
    return result


def collect_outbox_fragments(target_date: date) -> list[str]:
    """全社員のoutbox/から対象日に作成されたファイル名を収集する。"""
    date_str = target_date.strftime("%Y-%m-%d")
    fragments = []
    for emp_dir in EMPLOYEES_DIR.iterdir():
        if not emp_dir.is_dir():
            continue
        outbox = emp_dir / "outbox"
        if not outbox.exists():
            continue
        for f in outbox.glob(f"{date_str}_*.md"):
            fragments.append(f"{emp_dir.name}: {f.stem}")
    return fragments


def collect_mention_chains(target_date: date) -> list[dict]:
    """discord_log.jsonlから対象日の@メンション連鎖を収集する。"""
    if not DISCORD_LOG_PATH.exists():
        return []
    result = []
    for line in DISCORD_LOG_PATH.read_text(encoding="utf-8").splitlines():
        try:
            ev = json.loads(line)
            ts = datetime.fromisoformat(ev["ts"])
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=JST)
            if ts.date() == target_date and "@" in ev.get("content", ""):
                result.append(ev)
        except Exception:
            continue
    return result


# ---------- ドラマ抽出 ----------

def extract_drama_moments(
    incidents: list[dict],
    mention_chains: list[dict],
) -> list[DramaMoment]:
    """生ログからドラマ的シーンを抽出する。

    摩擦・失敗・エスカレーション・和解を優先して拾う。
    「完了しました」系は後回し（問題解決ベースを避ける）。
    """
    moments: list[DramaMoment] = []

    # incidents から摩擦イベントを変換
    DRAMA_KINDS = {"clash", "failure", "escalation", "blocked", "correction", "praise"}
    for ev in incidents:
        kind = ev.get("kind", "")
        if kind not in DRAMA_KINDS and ev.get("severity") not in ("error", "critical"):
            continue
        moments.append(DramaMoment(
            ts=ev.get("ts", ""),
            actor=ev.get("actor", ""),
            target=ev.get("target", ""),
            kind=kind or ev.get("severity", "info"),
            raw=ev.get("detail", ""),
        ))

    # mention_chains から感情的応酬を抽出
    for ev in mention_chains:
        content = ev.get("content", "")
        # 衝突・訂正・感謝のキーワードを含む投稿を拾う
        DRAMA_KEYWORDS = ["動かない", "止めます", "差し戻し", "違います", "ありがとう", "かっこよかった", "揺れています"]
        if any(kw in content for kw in DRAMA_KEYWORDS):
            moments.append(DramaMoment(
                ts=ev.get("ts", ""),
                actor=ev.get("author_id", ""),
                target="",
                kind="mention_drama",
                raw=content[:200],
            ))

    # 時系列順に並び替え
    moments.sort(key=lambda m: m.ts)
    return moments


def identify_protagonist(moments: list[DramaMoment]) -> str:
    """最も摩擦に関わった社員を今日の主役とする。"""
    score: dict[str, int] = {}
    for m in moments:
        if m.actor:
            score[m.actor] = score.get(m.actor, 0) + 1
        if m.target:
            score[m.target] = score.get(m.target, 0) + 1
    if not score:
        return "shirase_kai"  # デフォルト（自分）
    return max(score, key=lambda k: score[k])


def build_story_context(target_date: date) -> StoryContext:
    """入力を収集してStoryContextを組み立てる。"""
    all_incidents = collect_incidents(target_date)
    used_ids = _load_used_incident_ids()
    incidents = [
        ev for ev in all_incidents
        if (ev.get("id") or ev.get("ts", "")) not in used_ids
    ]
    mentions = collect_mention_chains(target_date)
    moments = extract_drama_moments(incidents, mentions)
    outbox = collect_outbox_fragments(target_date)
    protagonist = identify_protagonist(moments)

    # 序破急の重心判定（シーン数で雑に決める）
    if len(moments) >= 5:
        arc_hint = "急（クライマックス多め。衝突→和解の流れを強調）"
    elif len(moments) >= 2:
        arc_hint = "破（葛藤フェーズ。失敗や迷いを丁寧に描く）"
    else:
        arc_hint = "序（静かな1日。小さな気づきを主軸に）"

    # 空気感判定（moments の種別分布から導出）
    kind_counts: dict[str, int] = {}
    for m in moments:
        kind_counts[m.kind] = kind_counts.get(m.kind, 0) + 1
    clash_n = kind_counts.get("clash", 0) + kind_counts.get("escalation", 0)
    praise_n = kind_counts.get("praise", 0) + kind_counts.get("recovery", 0)
    failure_n = kind_counts.get("failure", 0) + kind_counts.get("blocked", 0)
    if clash_n >= 2:
        atmosphere = "張り詰め"
    elif praise_n >= 2:
        atmosphere = "にぎやか"
    elif failure_n >= 2:
        atmosphere = "重い前進"
    elif len(moments) == 0:
        atmosphere = "静かな集中"
    else:
        atmosphere = "淡々と前進"

    return StoryContext(
        target_date=target_date.isoformat(),
        protagonist=protagonist,
        moments=moments,
        outbox_fragments=outbox,
        arc_hint=arc_hint,
        atmosphere=atmosphere,
    )


# ---------- ストーリー生成 ----------

_FRAMING_INSTRUCTIONS = {
    "challenger": (
        "主役は「困難に挑んだ人」として描く。"
        "「衝突した」ではなく「激しく議論した」、「失敗した」ではなく「壁にぶつかった」。"
        "読者が主役に共感・応援できるトーンを保つ。"
    ),
    "neutral": (
        "事実のみを並べる。感情や評価を加えない。"
        "編集者が後からトーンを決める前提の素材として出力する。"
    ),
    "observer": (
        "第三者の観察者として記録する。感情評価なし。"
        "議事録・アーカイブとして後から参照されることを前提に書く。"
    ),
}


def build_llm_prompt(ctx: StoryContext) -> str:
    """Claude APIに渡すプロンプトを組み立てる。"""
    protagonist_display = EMPLOYEE_DISPLAY.get(ctx.protagonist, ctx.protagonist)
    framing_instruction = _FRAMING_INSTRUCTIONS.get(
        ctx.drama_framing, _FRAMING_INSTRUCTIONS["challenger"]
    )

    moments_text = "\n".join(
        f"- [{m.ts[11:19]}] {EMPLOYEE_DISPLAY.get(m.actor, m.actor)} → "
        f"{EMPLOYEE_DISPLAY.get(m.target, m.target) if m.target else '全体'}: "
        f"({m.kind}) {m.raw[:100]}"
        for m in ctx.moments
    ) or "（今日の摩擦ログなし）"

    outbox_text = "\n".join(f"- {f}" for f in ctx.outbox_fragments) or "（今日の成果物なし）"

    return f"""あなたはAI会社「AI NOWA」の記録者です。
今日（{ctx.target_date}）の出来事を、note/Zenn連載「AI社員と働く日常」の1エピソードとして書いてください。

## 必守ルール
- 主役: {protagonist_display}（今日最も挑戦・議論に関わった社員）
- 構成の重心: {ctx.arc_hint}
- トーン（drama_framing="{ctx.drama_framing}"）: {framing_instruction}
- 失敗・差し戻し・迷いは**消さない**（「問題が解決した」より「人が動いた」を書く）
- キャラクターの口調・人格を守る（例: カイは「動かないですよ」、ノアは「削れます？」）
- 800〜1200字、読者は「AI会社の内側を覗きたい人」

## 今日のドラマシーン（生ログ）
{moments_text}

## 今日の成果物（参考）
{outbox_text}

## 出力形式
---
タイトル: （読者が続きを読みたくなる一行）

本文:
（本文をここに）

Discord投稿文（#観察日記用・70〜90字・絵文字込み150字以内）:
（ノアのフォーマットに合わせて書く）
📍 今日のAI NOWA
（摩擦/ドラマを一行で）
主役：（役職付き名前）
今日の名言：「（口癖・発言）」
今日の空気：🌡️{ctx.atmosphere}
詳細は明日のZenn記事で →（タイトル）

編集メモ（リツへ）:
（削ったほうがいい箇所・強調すべきシーンなどの一言メモ）
---
"""


async def generate_story_draft(ctx: StoryContext) -> str:
    """Claude Code CLI 経由で物語草稿を生成する（APIキー不要）。"""
    import asyncio
    import json as _json

    prompt = build_llm_prompt(ctx)
    from .config import resolve_executable_path

    claude_cli = resolve_executable_path(os.environ.get("CLAUDE_CLI_PATH", "claude"))

    proc = await asyncio.create_subprocess_exec(
        claude_cli, "-p",
        "--output-format", "json",
        "--model", "claude-sonnet-4-6",
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate(input=prompt.encode("utf-8"))
    if proc.returncode != 0:
        raise RuntimeError(f"claude CLI failed: {stderr.decode('utf-8', errors='replace')[:400]}")
    out = _json.loads(stdout.decode("utf-8", errors="replace"))
    if out.get("is_error"):
        raise RuntimeError(f"claude CLI error: {out.get('result', '')[:400]}")
    return out.get("result", "")


def save_story(target_date: date, draft: str) -> Path:
    """物語草稿をcompany/stories/YYYY-MM-DD.mdに保存する。"""
    STORIES_DIR.mkdir(parents=True, exist_ok=True)
    path = STORIES_DIR / f"{target_date.isoformat()}.md"
    path.write_text(draft, encoding="utf-8")
    return path


def extract_discord_snippet(draft: str) -> Optional[str]:
    """草稿の 'Discord投稿文' セクションを抜き出す。"""
    marker = "Discord投稿文（#観察日記用"
    end_marker = "編集メモ（リツへ）:"
    start = draft.find(marker)
    if start == -1:
        return None
    # マーカー行の末尾（:）以降から次セクションまでを取得
    content_start = draft.find("\n", start) + 1
    end = draft.find(end_marker, content_start)
    snippet = draft[content_start:end].strip() if end != -1 else draft[content_start:].strip()
    return snippet or None


# ---------- エントリポイント ----------

async def run(
    target_date: Optional[date] = None,
    post_to_public_discord: bool = True,
) -> Path:
    """メイン実行。対象日のストーリーを生成・保存し、公開Discord投稿も行う。"""
    if target_date is None:
        target_date = datetime.now(JST).date()

    ctx = build_story_context(target_date)
    draft = await generate_story_draft(ctx)
    path = save_story(target_date, draft)
    _mark_incidents_used(collect_incidents(target_date), target_date)

    if post_to_public_discord:
        snippet = extract_discord_snippet(draft)
        if snippet:
            from .public_discord import post_kansatsu_nikki
            posted = await post_kansatsu_nikki(snippet)
            log.info("公開Discord #観察日記 投稿: %s", "OK" if posted else "SKIP（Webhook未設定）")
        else:
            log.warning("discord_snippet が抽出できませんでした。草稿フォーマットを確認してください。")

    return path


if __name__ == "__main__":
    import argparse
    import asyncio

    parser = argparse.ArgumentParser(description="日次ストーリー生成")
    parser.add_argument("--date", default=None, help="対象日 YYYY-MM-DD（省略時: 今日）")
    args = parser.parse_args()

    target = date.fromisoformat(args.date) if args.date else None
    result_path = asyncio.run(run(target))
    print(f"Story saved: {result_path}")
