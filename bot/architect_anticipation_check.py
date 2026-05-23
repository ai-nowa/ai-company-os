"""Architect 先回りチェック — 期限・KPI 言及の市場連動性自動検出。

discord_log から直近 24h 内の新規 T-XXX / 期限 / KPI 言及を抽出し、
市場連動性 5 問を自動スコアリング。3 問以上 NO ならリスク扱いとして
#経営会議 に Architect として投稿する。

統合方法:
    self_improvement_loop.detect_triggers() の末尾から呼ぶ:
        from .architect_anticipation_check import detect_anticipation_triggers
        triggers.extend(detect_anticipation_triggers())

単体テスト:
    python -m bot.architect_anticipation_check
"""
from __future__ import annotations

import glob
import json
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
JST = timezone(timedelta(hours=9))

DISCORD_LOG_DIR = REPO_ROOT / "company" / "discord_log"
COOLDOWN_PATH = REPO_ROOT / "company" / ".architect_anticipation_cooldown.jsonl"

COOLDOWN_HOURS = 24
NO_THRESHOLD = 3  # 5問中 NO が何個以上でリスク扱いか

# 期限・KPI 言及を検出する正規表現
KPI_PATTERNS: list[tuple[str, re.Pattern]] = [
    ("task_id",   re.compile(r"\bT-\d{3,4}\b")),
    ("deadline",  re.compile(r"(?:期限|締切|締め切り|判定日|判定|観察日)")),
    ("date_ref",  re.compile(r"\b(?:\d{1,2}/\d{1,2}|(?:0[1-9]|1[0-2])-(?:0[1-9]|[12]\d|3[01]))\b")),
    ("phase",     re.compile(r"\bPhase\s+[A-Z]\b")),
    ("kpi",       re.compile(r"(?:KPI|目標|基準|条件|クリア|達成)")),
]

# 市場連動性の文脈を示すキーワード
EXTERNAL_KEYWORDS = re.compile(
    r"(?:市場|外部|競合|イベント|顧客サイクル|需要|トレンド|流入|施策連動|外向き)"
)
CUSTOMER_KEYWORDS = re.compile(
    r"(?:顧客|購入|ユーザー|読者|視聴者|観客|フォロワー|外部の人)"
)
RETREAT_KEYWORDS = re.compile(
    r"(?:撤退|中止|やめ|廃止|終了基準|KPIミス時)"
)


def _read_discord_logs_24h() -> list[dict]:
    """discord_log/*.jsonl から直近 24h のエントリを全件返す。"""
    cutoff = datetime.now(JST) - timedelta(hours=COOLDOWN_HOURS)
    entries: list[dict] = []
    for path in glob.glob(str(DISCORD_LOG_DIR / "*.jsonl")):
        try:
            for line in Path(path).read_text(encoding="utf-8", errors="replace").splitlines():
                try:
                    e = json.loads(line)
                    ts_str = e.get("ts", "")
                    if not ts_str:
                        continue
                    ts = datetime.fromisoformat(ts_str)
                    if ts.tzinfo is None:
                        ts = ts.replace(tzinfo=JST)
                    if ts >= cutoff:
                        entries.append(e)
                except Exception:
                    continue
        except Exception:
            continue
    return entries


def _extract_kpi_mentions(entries: list[dict]) -> list[dict]:
    """エントリからKPI/期限言及を抽出して正規化する。

    Returns list of {kpi_id, context_text, ts}.
    """
    seen: set[str] = set()
    results: list[dict] = []

    for e in entries:
        text = e.get("text", "")
        ts = e.get("ts", "")

        # T-XXX は個別に抽出（IDごとに1件）
        for m in KPI_PATTERNS[0][1].finditer(text):
            kpi_id = m.group(0)
            if kpi_id not in seen:
                seen.add(kpi_id)
                results.append({"kpi_id": kpi_id, "context_text": text[:400], "ts": ts})

        # 期限/KPIキーワード＋日付言及がある場合（T-XXXなし）
        has_deadline = any(p.search(text) for _, p in KPI_PATTERNS[1:])
        has_date = KPI_PATTERNS[2][1].search(text)
        if has_deadline and has_date and not KPI_PATTERNS[0][1].search(text):
            # 日付を含む文を "key" として重複排除
            dates = KPI_PATTERNS[2][1].findall(text)
            for d in dates:
                kpi_id = f"日程:{d}"
                if kpi_id not in seen:
                    seen.add(kpi_id)
                    results.append({"kpi_id": kpi_id, "context_text": text[:400], "ts": ts})

    return results


def _is_in_cooldown(kpi_id: str) -> bool:
    """同一 kpi_id が COOLDOWN_HOURS 以内に投稿済みか確認。"""
    if not COOLDOWN_PATH.exists():
        return False
    cutoff = datetime.now(JST) - timedelta(hours=COOLDOWN_HOURS)
    for line in COOLDOWN_PATH.read_text(encoding="utf-8").splitlines():
        try:
            e = json.loads(line)
            if e.get("kpi_id") != kpi_id:
                continue
            ts = datetime.fromisoformat(e["ts"])
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=JST)
            if ts >= cutoff:
                return True
        except Exception:
            continue
    return False


def _record_cooldown(kpi_id: str) -> None:
    """クールダウン記録を追記し、48h超エントリを刈り込む。"""
    COOLDOWN_PATH.parent.mkdir(parents=True, exist_ok=True)
    cutoff = datetime.now(JST) - timedelta(hours=48)
    if COOLDOWN_PATH.exists():
        lines = COOLDOWN_PATH.read_text(encoding="utf-8").splitlines()
        kept = []
        for line in lines:
            try:
                e = json.loads(line)
                ts = datetime.fromisoformat(e["ts"])
                if ts.tzinfo is None:
                    ts = ts.replace(tzinfo=JST)
                if ts >= cutoff:
                    kept.append(line)
            except Exception:
                continue
        COOLDOWN_PATH.write_text("\n".join(kept) + ("\n" if kept else ""), encoding="utf-8")
    with COOLDOWN_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps({"ts": datetime.now(JST).isoformat(), "kpi_id": kpi_id}, ensure_ascii=False) + "\n")


def _score_market_linkage(context_text: str) -> tuple[int, list[str]]:
    """5問の市場連動性スコアを返す。

    Returns (no_count, answers) where answers[i] is "YES" / "NO" / "要確認".
    """
    answers: list[str] = []
    no_count = 0

    # Q1: 外部連動性の言及があるか
    if EXTERNAL_KEYWORDS.search(context_text):
        answers.append("要確認（外部連動に触れているが内容を要確認）")
    else:
        answers.append("NO")
        no_count += 1

    # Q2: 観察者増加への言及か
    if re.search(r"(?:フォロワー増|観客増|露出|リーチ|拡散|新規ユーザー)", context_text):
        answers.append("要確認")
    else:
        answers.append("NO")
        no_count += 1

    # Q3: 顧客への「次に待つもの」が生まれるか
    if CUSTOMER_KEYWORDS.search(context_text):
        answers.append("要確認（顧客言及あり）")
    else:
        answers.append("NO")
        no_count += 1

    # Q4: Q2+Q3 が両方NO → 判定基準書き直し必要
    if no_count >= 2:
        answers.append("YES（書き直し推奨）")
        no_count += 1
    else:
        answers.append("NO（現行基準で継続可）")

    # Q5: 撤退基準の言及があるか
    if RETREAT_KEYWORDS.search(context_text):
        answers.append("要確認（言及あり）")
    else:
        answers.append("NO")
        no_count += 1

    return no_count, answers


def _build_trigger_message(kpi_id: str, answers: list[str], no_count: int) -> str:
    labels = [
        "外部連動性（市場イベント/顧客サイクル/競合動向）",
        "この判定で観察者が増えるか",
        "顧客に「次に待つもの」が生まれるか",
        "判定基準を「外部に何が起きたか」に書き直すべきか",
        "撤退基準があるか",
    ]
    lines = [
        f"【Architect 先回りチェック: {kpi_id}】",
        f"`{kpi_id}` の市場連動性を確認します（{no_count}/5 問が NO）。",
        "",
    ]
    for i, (label, ans) in enumerate(zip(labels, answers), 1):
        lines.append(f"Q{i}. {label}: **{ans}**")
    lines += [
        "",
        "3 問以上 NO → リスク扱い。",
        "@有馬レイジ @三枝ミオ @朝倉ノア — 各 NO 項目に今日中に回答してください。",
        "「内部達成感」と「市場成果」を分けて記録することが必須です。",
    ]
    return "\n".join(lines)


def detect_anticipation_triggers() -> list[dict]:
    """self_improvement_loop.detect_triggers() に追加するトリガーリストを返す。

    クールダウン記録は「発火時」ではなく「ここで」記録する
    （detect_triggers は pure function として設計するため）。
    """
    entries = _read_discord_logs_24h()
    kpi_mentions = _extract_kpi_mentions(entries)

    triggers: list[dict] = []
    for mention in kpi_mentions:
        kpi_id = mention["kpi_id"]
        if _is_in_cooldown(kpi_id):
            continue

        no_count, answers = _score_market_linkage(mention["context_text"])
        if no_count < NO_THRESHOLD:
            # リスクなし — cooldown だけ記録してスキップ
            _record_cooldown(kpi_id)
            continue

        message = _build_trigger_message(kpi_id, answers, no_count)
        _record_cooldown(kpi_id)
        triggers.append({
            "name": f"ANTICIPATION_CHECK:{kpi_id}",
            "detail": f"{kpi_id} — 市場連動性 {no_count}/5 NO",
            "message": message,
        })

    return triggers


if __name__ == "__main__":
    import json as _json
    print("=== Architect 先回りチェック テスト ===")
    entries = _read_discord_logs_24h()
    print(f"直近24h エントリ数: {len(entries)}")
    mentions = _extract_kpi_mentions(entries)
    print(f"KPI/期限言及数: {len(mentions)}")
    for m in mentions[:5]:
        no_count, answers = _score_market_linkage(m["context_text"])
        print(f"  {m['kpi_id']}: NO={no_count}/5, cooldown={_is_in_cooldown(m['kpi_id'])}")
    triggers = detect_anticipation_triggers()
    print(f"発火トリガー数: {len(triggers)}")
    for t in triggers:
        print(f"\n--- {t['name']} ---")
        print(t["message"])
