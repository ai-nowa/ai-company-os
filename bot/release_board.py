"""Release pressure board for AI NOWA.

This module is intentionally cheap: it scans local files and Discord logs,
then turns "we made something" into "has a public URL / shipped path / next
release action". It does not call an LLM.
"""
from __future__ import annotations

import asyncio
import json
import logging
import re
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from . import dynamic_config
from .config import BASE_DIR, COMPANY_DIR, EMPLOYEES, JST, now_jst_iso

log = logging.getLogger("release_board")

EMPLOYEES_DIR = BASE_DIR / "employees"
DISCORD_LOG_DIR = COMPANY_DIR / "discord_log"
IKUTO_REQ_LOG = DISCORD_LOG_DIR / "📥｜いくと依頼.jsonl"
OUTPUT_PATH = COMPANY_DIR / "release_board.md"
STATE_FILE = COMPANY_DIR / ".release_pressure_state.json"

PUBLIC_URL_RE = re.compile(r"https?://[^\s)>\]\"']+")
PUBLIC_HOST_RE = re.compile(
    r"(ai-nowa\.com|youtu\.be|youtube\.com|zenn\.dev|"
    r"github\.com/ai-nowa|bsky\.app|x\.com|twitter\.com|qiita\.com)",
    re.IGNORECASE,
)
LOCAL_OR_DRAFT_RE = re.compile(r"(localhost|127\.0\.0\.1|preview\.json|dry_run)", re.IGNORECASE)

READY_KEYWORDS = [
    "公開依頼", "投稿依頼", "公開GO", "公開をお願いします", "コピペOK", "投稿本文",
    "YouTube Shorts", "Xポスト", "記事", "article", "draft", "台本", "script",
    "CTA", "コピー", "説明欄", "動画", "mp4", "shop", "販売", "導線",
]
HUMAN_WAIT_KEYWORDS = [
    "いくと待ち", "投稿お願いします", "投稿をお願いします", "公開お願いします", "公開をお願いします",
    "投稿後", "コピペ", "X投稿", "YouTube", "Shorts", "note", "人間",
]
INTERNAL_ONLY_NAME_RE = re.compile(
    r"(ack|ceo|decision|judgment|handover|praise|findings|review|audit|"
    r"measure|measurement|state_correction|scope)",
    re.IGNORECASE,
)
KEY_RELEASE_EMPLOYEES = {
    "arima_reiji",
    "saegusa_mio",
    "asakura_noa",
    "kuroba_yuu",
    "hoshino_ritsu",
    "shirase_kai",
    "kagura_aoi",
}


@dataclass
class PublicOutput:
    ts: str
    source: str
    url: str
    label: str


@dataclass
class ReleaseCandidate:
    path: str
    employee_id: str
    kind: str
    age_hours: float
    priority: int
    title: str
    suggested_action: str


@dataclass
class HumanWaitRequest:
    ts: str
    employee_id: str
    author: str
    kind: str
    text: str
    suggested_action: str


def _now() -> datetime:
    return datetime.now(JST)


def _short(text: str, limit: int = 180) -> str:
    text = re.sub(r"\s+", " ", str(text)).strip()
    if len(text) <= limit:
        return text
    return text[: max(0, limit - 1)].rstrip() + "…"


def _parse_ts(value: str) -> datetime | None:
    if not value:
        return None
    try:
        ts = datetime.fromisoformat(value)
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=JST)
        return ts.astimezone(JST)
    except Exception:
        return None


def _read_jsonl(path: Path, limit: int = 500) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    events: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines()[-limit:]:
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return events


def _rel(path: Path) -> str:
    try:
        return str(path.relative_to(BASE_DIR))
    except ValueError:
        return str(path)


def _file_mtime(path: Path) -> datetime:
    return datetime.fromtimestamp(path.stat().st_mtime, JST)


def _public_urls(text: str) -> list[str]:
    urls: list[str] = []
    for raw in PUBLIC_URL_RE.findall(text or ""):
        url = raw.rstrip(".,、。)`）")
        if LOCAL_OR_DRAFT_RE.search(url):
            continue
        if PUBLIC_HOST_RE.search(url):
            urls.append(url)
    return list(dict.fromkeys(urls))


def _candidate_kind(path: Path, text: str) -> str:
    name = path.name.lower()
    if path.suffix.lower() == ".mp4" or any(token in name for token in ("video", "youtube", "shorts", "script")):
        return "video"
    if "x_post" in name or "x_" in name or "twitter" in name:
        return "x_post"
    if "article" in name or "zenn" in name:
        return "article"
    if any(token in name for token in ("shop", "cta", "copy", "sales")):
        return "sales_page"
    hay = f"{path.name}\n{text}"
    if "YouTube" in hay or "Shorts" in hay:
        return "video"
    if "Xポスト" in hay or "X投稿" in hay or "twitter" in hay.lower():
        return "x_post"
    if "article" in hay.lower() or "記事" in hay or "Zenn" in hay:
        return "article"
    if "shop" in hay.lower() or "販売" in hay or "CTA" in hay:
        return "sales_page"
    return "artifact"


def _employee_from_path(path: Path) -> str:
    parts = path.parts
    try:
        i = parts.index("employees")
        return parts[i + 1]
    except (ValueError, IndexError):
        return "shared"


def _candidate_title(path: Path, text: str) -> str:
    for line in text.splitlines()[:20]:
        s = line.strip()
        if s.startswith("#"):
            return _short(s.lstrip("# ").strip(), 80)
        if "タイトル" in s and ":" in s:
            return _short(s.split(":", 1)[1], 80)
    return path.name


def _suggest_action(kind: str, path: str, text: str = "") -> str:
    try:
        from .output_routes import route_for_kind

        return route_for_kind(kind)
    except Exception:
        if kind == "video":
            token = BASE_DIR / "bot" / "youtube_token.json"
            if token.exists():
                return "YouTube OAuthあり。公開/限定公開URLを作り、URLを成果物報告へ記録する。"
            return "YouTubeが無理なら、動画の静止画+本文をサイト記事かDiscord公開サーバーへ即転用する。"
        if kind == "x_post":
            return "Xが人間待ちなら止めず、同文をサイト短報・Bluesky・Qiita/Zenn導線のどれかへ転用する。"
        if kind == "article":
            return "監査済みなら site/public/articles へ反映し、公開URLと導線CTAを成果物報告へ出す。"
        if kind == "sales_page":
            return "ai-nowa.com/shop への導線を1本増やし、/shop PVを今日の最小成功にする。"
        return "内部メモで止めず、公開URL・販売導線・投稿本文のどれかへ変換する。"


def collect_public_outputs(hours: int = 24) -> list[PublicOutput]:
    cutoff = _now() - timedelta(hours=hours)
    outputs: list[PublicOutput] = []

    for path in sorted(DISCORD_LOG_DIR.glob("*.jsonl")):
        for event in _read_jsonl(path, limit=800):
            ts = _parse_ts(str(event.get("ts", "")))
            if not ts or ts < cutoff:
                continue
            text = str(event.get("text", ""))
            for url in _public_urls(text):
                outputs.append(PublicOutput(
                    ts=ts.isoformat(),
                    source=path.stem,
                    url=url,
                    label=_short(text, 90),
                ))

    upload_dir = BASE_DIR / "shared" / "media" / "upload_results"
    if upload_dir.exists():
        for path in upload_dir.glob("*.json"):
            try:
                if _file_mtime(path) < cutoff:
                    continue
                data = json.loads(path.read_text(encoding="utf-8", errors="replace"))
            except Exception:
                continue
            url = str(data.get("url") or "")
            if url and _public_urls(url):
                outputs.append(PublicOutput(
                    ts=_file_mtime(path).isoformat(),
                    source=_rel(path),
                    url=url,
                    label=_short(data.get("title") or path.name, 90),
                ))

    unique: dict[str, PublicOutput] = {}
    for item in outputs:
        unique.setdefault(item.url, item)
    return sorted(unique.values(), key=lambda x: x.ts, reverse=True)


def collect_ready_candidates(hours: int = 48) -> list[ReleaseCandidate]:
    cutoff = _now() - timedelta(hours=hours)
    roots = [
        BASE_DIR / "shared" / "media" / "videos",
    ]
    roots.extend(sorted(EMPLOYEES_DIR.glob("*/outbox")))
    candidates: list[ReleaseCandidate] = []
    for root in roots:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if not path.is_file() or any(part in {"_archive", "archive", "__pycache__"} for part in path.parts):
                continue
            if path.suffix.lower() not in {".md", ".mp4", ".html", ".txt"}:
                continue
            try:
                mtime = _file_mtime(path)
            except OSError:
                continue
            if mtime < cutoff:
                continue
            text = ""
            if path.suffix.lower() != ".mp4":
                try:
                    text = path.read_text(encoding="utf-8", errors="replace")[:5000]
                except Exception:
                    text = ""
            hay = f"{path.name}\n{text}"
            if not any(keyword.lower() in hay.lower() for keyword in READY_KEYWORDS):
                continue
            has_publish_language = any(
                keyword in hay
                for keyword in ("公開依頼", "投稿依頼", "公開GO", "投稿本文", "コピペOK", "YouTube", "Xポスト")
            )
            if INTERNAL_ONLY_NAME_RE.search(path.name) and not has_publish_language:
                continue

            kind = _candidate_kind(path, text)
            age = round((_now() - mtime).total_seconds() / 3600, 1)
            priority = 100
            if has_publish_language:
                priority += 40
            if kind in {"video", "x_post", "article", "sales_page"}:
                priority += 20
            if age >= 2:
                priority += 20
            candidates.append(ReleaseCandidate(
                path=_rel(path),
                employee_id=_employee_from_path(path),
                kind=kind,
                age_hours=age,
                priority=priority,
                title=_candidate_title(path, text),
                suggested_action=_suggest_action(kind, _rel(path), text),
            ))

    candidates.sort(key=lambda c: (c.priority, -c.age_hours), reverse=True)
    return candidates[:30]


def _wait_kind(text: str) -> str:
    if "YouTube" in text or "Shorts" in text or "動画" in text:
        return "video"
    if "X" in text or "ポスト" in text or "投稿本文" in text:
        return "x_post"
    if "記事" in text or "Zenn" in text or "note" in text:
        return "article"
    if "shop" in text or "販売" in text or "Polar" in text:
        return "sales_page"
    return "owner_wait"


def collect_human_wait_requests(hours: int = 24) -> list[HumanWaitRequest]:
    cutoff = _now() - timedelta(hours=hours)
    requests: list[HumanWaitRequest] = []
    for event in _read_jsonl(IKUTO_REQ_LOG, limit=500):
        ts = _parse_ts(str(event.get("ts", "")))
        if not ts or ts < cutoff:
            continue
        if event.get("kind") not in {"employee", "architect"}:
            continue
        text = str(event.get("text", ""))
        if not any(keyword in text for keyword in HUMAN_WAIT_KEYWORDS):
            continue
        kind = _wait_kind(text)
        requests.append(HumanWaitRequest(
            ts=ts.isoformat(),
            employee_id=str(event.get("employee_id") or "unknown"),
            author=str(event.get("author") or "?"),
            kind=kind,
            text=_short(text, 220),
            suggested_action=_suggest_action(kind, "", text),
        ))
    return sorted(requests, key=lambda r: r.ts, reverse=True)


def collect_release_metrics() -> dict[str, Any]:
    public_outputs = collect_public_outputs(hours=24)
    candidates = collect_ready_candidates(hours=72)
    human_waits = collect_human_wait_requests(hours=24)
    stale_candidates = [c for c in candidates if c.age_hours >= 2]
    return {
        "ts": now_jst_iso(),
        "public_outputs_24h": len(public_outputs),
        "ready_to_ship_count": len(candidates),
        "stale_ready_count": len(stale_candidates),
        "human_wait_requests_24h": len(human_waits),
        "output_debt": max(0, len(candidates) + len(human_waits) - len(public_outputs)),
        "latest_public_outputs": [asdict(x) for x in public_outputs[:8]],
        "top_candidates": [asdict(x) for x in candidates[:8]],
        "human_waits": [asdict(x) for x in human_waits[:8]],
    }


def release_digest(max_chars: int = 900, employee_id: str | None = None) -> str:
    metrics = collect_release_metrics()
    lines = [
        f"- public_outputs_24h: {metrics['public_outputs_24h']}",
        f"- ready_to_ship: {metrics['ready_to_ship_count']} / stale_2h+: {metrics['stale_ready_count']}",
        f"- human_wait_requests_24h: {metrics['human_wait_requests_24h']}",
        "- rule: 内部メモは成果ではない。公開URL・販売導線・投稿URL・計測可能なデプロイを成果に数える。",
        "- rule: 日付/明朝/24h後は待機理由ではない。公開待ち候補があるなら今、別チャネルで出す。",
        "- template: shared/templates/output_playbook.md",
    ]
    top_candidates = metrics.get("top_candidates", [])
    if employee_id and employee_id not in KEY_RELEASE_EMPLOYEES:
        top_candidates = [c for c in top_candidates if c.get("employee_id") == employee_id]
    if top_candidates:
        lines.append("- ready:")
        for c in top_candidates[:3]:
            lines.append(
                f"  - {c['kind']} {c['path']} age={c['age_hours']}h -> {_short(c['suggested_action'], 100)}"
            )
    human_waits = metrics.get("human_waits", [])
    if human_waits and (not employee_id or employee_id in KEY_RELEASE_EMPLOYEES):
        lines.append("- human_wait_to_replace:")
        for req in human_waits[:2]:
            lines.append(f"  - {req['kind']} {req['ts'][11:16]} {req['author']} -> {_short(req['suggested_action'], 100)}")
    text = "\n".join(lines)
    if len(text) <= max_chars:
        return text
    return text[: max(0, max_chars - 24)].rstrip() + "\n- ...(truncated)"


def release_wake_items(employee_id: str, max_items: int = 3) -> list[str]:
    if employee_id not in KEY_RELEASE_EMPLOYEES:
        return []
    metrics = collect_release_metrics()
    items: list[str] = []
    for c in metrics.get("top_candidates", [])[:max_items]:
        items.append(f"- ready_to_ship: {c['kind']} {c['path']} age={c['age_hours']}h")
    for req in metrics.get("human_waits", [])[:max(0, max_items - len(items))]:
        items.append(f"- human_wait_replace: {req['kind']} {req['ts'][11:16]} {req['author']}")
    return items


def render_release_board(metrics: dict[str, Any] | None = None) -> str:
    metrics = metrics or collect_release_metrics()
    lines = [
        "# Release Board",
        "",
        f"自動生成: {metrics.get('ts', now_jst_iso())}",
        "",
        "## Scoreboard",
        "",
        "| 指標 | 値 | 解釈 |",
        "|---|---:|---|",
        f"| public_outputs_24h | {metrics['public_outputs_24h']} | 24h以内にURL/公開導線として確認できた成果 |",
        f"| ready_to_ship | {metrics['ready_to_ship_count']} | 出せる材料。ここが多いほど未出荷在庫 |",
        f"| stale_ready_2h+ | {metrics['stale_ready_count']} | 2h以上公開待ち。待機ではなく負債 |",
        f"| human_wait_requests_24h | {metrics['human_wait_requests_24h']} | 人間待ち化した公開/投稿依頼 |",
        f"| output_debt | {metrics['output_debt']} | ready + human_wait - public_output |",
        "",
        "## Operating Rule",
        "",
        "- 内部メモ、承認ログ、判断ファイルは公開成果に数えない。",
        "- Xなど単一チャネルが人間待ちなら、同じ素材をYouTube/Zenn/site/Bluesky/Qiita/Discord公開導線へ転用する。",
        "- 判定日・明朝・24h後は待機日ではない。公開待ち候補がある限り今出す。",
        "",
        "## Ready To Ship",
        "",
    ]
    candidates = metrics.get("top_candidates", [])
    if candidates:
        lines.extend(["| 種別 | 経過 | 所有 | パス | 次の即時行動 |", "|---|---:|---|---|---|"])
        for c in candidates[:10]:
            display = EMPLOYEES.get(c.get("employee_id", ""), {}).get("display", c.get("employee_id", "?"))
            lines.append(
                f"| {c['kind']} | {c['age_hours']}h | {display} | `{c['path']}` | {_short(c['suggested_action'], 100)} |"
            )
    else:
        lines.append("- なし")

    lines.extend(["", "## Human Wait To Replace", ""])
    waits = metrics.get("human_waits", [])
    if waits:
        lines.extend(["| 時刻 | 起票者 | 種別 | 代替行動 |", "|---|---|---|---|"])
        for req in waits[:10]:
            lines.append(
                f"| {req['ts'][:16].replace('T', ' ')} | {req['author']} | {req['kind']} | {_short(req['suggested_action'], 100)} |"
            )
    else:
        lines.append("- なし")

    lines.extend(["", "## Latest Public Outputs", ""])
    outputs = metrics.get("latest_public_outputs", [])
    if outputs:
        for out in outputs[:10]:
            lines.append(f"- {out['ts'][:16].replace('T', ' ')} `{out['source']}` {out['url']}")
    else:
        lines.append("- なし")

    return "\n".join(lines) + "\n"


def write_release_board(metrics: dict[str, Any] | None = None) -> Path:
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(render_release_board(metrics), encoding="utf-8")
    return OUTPUT_PATH


def _load_state() -> dict[str, Any]:
    try:
        if STATE_FILE.exists():
            return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except Exception:
        pass
    return {}


def _save_state(state: dict[str, Any]) -> None:
    STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def _signature(metrics: dict[str, Any]) -> str:
    candidate_keys = [c.get("path", "") for c in metrics.get("top_candidates", [])[:5]]
    wait_keys = [w.get("ts", "") + w.get("kind", "") for w in metrics.get("human_waits", [])[:5]]
    return "|".join([
        str(metrics.get("public_outputs_24h", 0)),
        ";".join(candidate_keys),
        ";".join(wait_keys),
    ])


def _should_alert(metrics: dict[str, Any], state: dict[str, Any]) -> bool:
    if metrics.get("ready_to_ship_count", 0) == 0 and metrics.get("human_wait_requests_24h", 0) == 0:
        return False
    if metrics.get("output_debt", 0) <= 0 and metrics.get("human_wait_requests_24h", 0) == 0:
        return False
    sig = _signature(metrics)
    if sig != state.get("last_signature"):
        return True
    last = _parse_ts(str(state.get("last_alert_ts", "")))
    cooldown_min = int(dynamic_config.get("release_pressure.cooldown_minutes", 90))
    return last is None or (_now() - last).total_seconds() >= cooldown_min * 60


def format_release_alert(metrics: dict[str, Any]) -> str:
    candidates = metrics.get("top_candidates", [])
    waits = metrics.get("human_waits", [])
    lines = [
        "【Release Pressure: 未出荷在庫あり】",
        f"public_outputs_24h={metrics['public_outputs_24h']} / ready={metrics['ready_to_ship_count']} / human_wait={metrics['human_wait_requests_24h']} / debt={metrics['output_debt']}",
        "",
        "方針: いくと待ち・明朝待ちで止めない。公開URL、販売導線、投稿URL、または計測可能なデプロイに今変換してください。",
    ]
    if candidates:
        lines.append("")
        lines.append("優先候補:")
        for c in candidates[:3]:
            lines.append(f"- {c['kind']} `{c['path']}` ({c['age_hours']}h): {_short(c['suggested_action'], 120)}")
    if waits:
        lines.append("")
        lines.append("人間待ち置換:")
        for req in waits[:2]:
            lines.append(f"- {req['kind']} {req['author']}: {_short(req['suggested_action'], 120)}")
    lines.append("")
    lines.append("@有馬レイジ @三枝ミオ @朝倉ノア — 次の発言は会議ではなく、出荷担当・URL/パス・計測条件の確定にしてください。")
    return "\n".join(lines)


async def release_pressure_loop() -> None:
    interval = int(dynamic_config.get("release_pressure.interval_seconds", 1800))
    initial_delay = int(dynamic_config.get("release_pressure.initial_delay_seconds", 180))
    log.info("release_pressure loop started (interval=%ss)", interval)
    await asyncio.sleep(initial_delay)
    while True:
        try:
            interval = int(dynamic_config.get("release_pressure.interval_seconds", 1800))
            metrics = collect_release_metrics()
            write_release_board(metrics)
            state = _load_state()
            if _should_alert(metrics, state):
                from .architect_outbox import submit_post

                submit_post("お知らせ", format_release_alert(metrics), label="release_pressure")
                state["last_alert_ts"] = now_jst_iso()
                state["last_signature"] = _signature(metrics)
                _save_state(state)
                log.info("release_pressure alert posted")
        except asyncio.CancelledError:
            return
        except Exception:
            log.exception("release_pressure loop error")
        await asyncio.sleep(interval)


if __name__ == "__main__":
    p = write_release_board()
    print(f"written: {p}")
    print(p.read_text(encoding="utf-8")[:3000])
