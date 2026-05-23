"""外部 URL の死活監視（社員に LLM を消費させない）。

LLM 呼ばない。Python の urllib のみ。
- company/watched_urls.json で監視対象を管理
- 30分ごとに HEAD リクエスト
- 状態変化（200→404 / 404→200）した時だけ📢に1回通知
- 同じ状態の連続報告は抑制
"""
from __future__ import annotations

import asyncio
import json
import logging
import urllib.request
import urllib.error
from datetime import datetime
from pathlib import Path

from .config import BASE_DIR, JST, now_jst_iso
from . import dynamic_config

log = logging.getLogger("external_check")

WATCHED_FILE = BASE_DIR / "company" / "watched_urls.json"
STATE_FILE = BASE_DIR / "company" / ".external_check_state.json"


def _load_watched() -> list[dict]:
    """[{url, label, owner}, ...] を返す。ファイルなければ空。"""
    if not WATCHED_FILE.exists():
        return []
    try:
        return json.loads(WATCHED_FILE.read_text(encoding="utf-8"))
    except Exception:
        log.exception(f"failed to parse {WATCHED_FILE}")
        return []


def _load_state() -> dict:
    if not STATE_FILE.exists():
        return {}
    try:
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save_state(state: dict) -> None:
    STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def _check_one(url: str) -> tuple[int, str]:
    """(status_code, note)。404 や接続失敗時もそのまま返す。"""
    req = urllib.request.Request(url, method="HEAD",
                                  headers={"User-Agent": "AI-NOWA-watcher/0.1"})
    timeout = dynamic_config.get("external_check.request_timeout", 10)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, "ok"
    except urllib.error.HTTPError as e:
        return e.code, f"http_error"
    except (urllib.error.URLError, TimeoutError) as e:
        return 0, f"conn_error:{type(e).__name__}"
    except Exception as e:
        return -1, f"unknown:{type(e).__name__}"


async def scan_loop() -> None:
    interval = dynamic_config.get("external_check.interval_seconds", 1800)
    log.info(f"external_check started (interval={interval}s, watched={WATCHED_FILE})")
    while True:
        try:
            interval = dynamic_config.get("external_check.interval_seconds", 1800)
            await asyncio.sleep(interval)
            watched = _load_watched()
            if not watched:
                continue
            state = _load_state()
            changed: list[str] = []
            for entry in watched:
                url = entry.get("url", "").strip()
                if not url:
                    continue
                label = entry.get("label", url)
                owner = entry.get("owner", "")
                status, note = await asyncio.to_thread(_check_one, url)
                prev = state.get(url, {}).get("status")
                state[url] = {"status": status, "note": note, "checked": now_jst_iso()}
                if prev is not None and prev != status:
                    arrow = f"{prev} → {status}"
                    changed.append(f"- {label} ({owner}): {arrow} [{note}] — {url}")
                    log.info(f"external_check change: {url} {arrow}")
            _save_state(state)

            if changed:
                from .architect_outbox import submit_post
                msg = (
                    "## 外部URL 状態変化（Architect / 自動監視）\n\n"
                    + "\n".join(changed)
                    + "\n\n復旧確認 or 別ルート検討を関連オーナーが判断してください。"
                )
                submit_post("お知らせ", msg, label="external_url_change")
        except asyncio.CancelledError:
            return
        except Exception:
            log.exception("external_check loop error")
            await asyncio.sleep(interval)


if __name__ == "__main__":
    # 単体テスト
    import sys
    watched = _load_watched()
    print(f"watched: {len(watched)} URLs")
    for entry in watched:
        url = entry.get("url", "")
        status, note = _check_one(url)
        print(f"  {status:4} [{note}] {url}")
