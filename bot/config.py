"""共通設定とファイルI/O。
全モジュールはここを起点にディレクトリ・社員情報・永続化関数にアクセスする。
"""
from __future__ import annotations

import json
import os
import shutil
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

import yaml
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env")

BASE_DIR = Path(os.environ.get("COMPANY_BASE_DIR", "/home/ikuto/ai-company-os"))
EMPLOYEES_DIR = BASE_DIR / "employees"
COMPANY_DIR = BASE_DIR / "company"
RELATIONSHIPS_DIR = BASE_DIR / "relationships"
DOCS_DIR = BASE_DIR / "docs"

JST = timezone(timedelta(hours=9))

# model: 社員別の基準モデル。Claude は alias を使い、具体バージョンは Claude Code 側に追従させる。
#        実際の model/effort は bot/model_policy.py と company/dynamic_config.yaml で最終決定する。
# default_channels: その社員がデフォルトで「見える」チャンネル名の部分一致パターン。
#                   "all" のみハル特例（People担当として全チャンネル閲覧可）
EMPLOYEES: dict[str, dict] = {
    "arima_reiji":   {"display": "有馬レイジ",   "role": "CEO",           "backend": "codex",  "model": "gpt-5.5",
                      "app_id": "1505056923546812548",
                      "default_channels": ["お知らせ", "経営会議", "全社会議", "今日の業務", "議事録", "給湯室", "いくと依頼"]},
    "saegusa_mio":   {"display": "三枝ミオ",     "role": "COO",           "backend": "claude", "model": "sonnet",
                      "app_id": "1505059351386390560",
                      "default_channels": ["お知らせ", "経営会議", "プロダクト会議", "今日の業務", "議事録", "ふりかえり", "給湯室", "モヤモヤ", "いくと依頼"]},
    "shirase_kai":   {"display": "白瀬カイ",     "role": "CTO",           "backend": "claude", "model": "sonnet",
                      "app_id": "1505059548350906528",
                      "default_channels": ["開発部", "プロダクト会議", "ひらめきメモ", "給湯室", "いくと依頼"]},
    "asakura_noa":   {"display": "朝倉ノア",     "role": "PM",            "backend": "claude", "model": "sonnet",
                      "app_id": "1505059712188682354",
                      "default_channels": ["経営会議", "プロダクト会議", "開発部", "youtube編集部", "成果物報告", "いくと依頼"]},
    "hoshino_ritsu": {"display": "星野リツ",     "role": "YouTube編集長", "backend": "claude", "model": "sonnet",
                      "app_id": "1505059860448804924",
                      "default_channels": ["youtube編集部", "マーケ部", "ひらめきメモ", "給湯室", "いくと依頼"]},
    "kuroba_yuu":    {"display": "黒羽ユウ",     "role": "マーケター",    "backend": "claude", "model": "sonnet",
                      "app_id": "1505060016296820818",
                      "default_channels": ["マーケ部", "youtube編集部", "成果物報告", "給湯室", "いくと依頼"]},
    "kagura_aoi":    {"display": "神楽アオイ",   "role": "監査",          "backend": "claude", "model": "sonnet",
                      "app_id": "1505060175323725854",
                      "default_channels": ["監査部", "プロダクト会議", "お知らせ", "成果物報告", "いくと依頼"]},
    "morinaga_haru": {"display": "森永ハル",     "role": "People",        "backend": "claude", "model": "sonnet",
                      "app_id": "1505060357008523284",
                      "default_channels": ["all"]},  # ハル特例: 全チャンネル閲覧可
    "hinata_nagi":   {"display": "日向ナギ",     "role": "視聴者代表",    "backend": "claude", "model": "sonnet",
                      "app_id": "1505060520695169035",
                      "default_channels": ["youtube編集部", "マーケ部", "見学者向け", "給湯室", "会社案内", "いくと依頼"]},
}

DISPLAY_TO_ID = {v["display"]: k for k, v in EMPLOYEES.items()}

def resolve_executable_path(command: str) -> str:
    """CLI executable を PATH / common local install locations から解決する。

    nvm 管理の `claude`/`codex` は再起動タイミングや systemd/手元 shell の PATH 差で
    見えなくなることがある。実行直前にもこの関数を通すことで、一時的な PATH 差で
    社員応答が system_error になる確率を下げる。
    """
    expanded = os.path.expanduser(str(command))
    name = Path(expanded).name

    if os.path.isabs(expanded) and os.access(expanded, os.X_OK):
        return expanded

    resolved = shutil.which(expanded)
    if resolved:
        return resolved

    search_paths: list[Path] = [
        Path.home() / ".local" / "bin" / name,
        Path("/usr/local/bin") / name,
        Path("/usr/bin") / name,
    ]

    nvm_root = Path.home() / ".nvm" / "versions" / "node"
    if nvm_root.exists():
        def _node_version_key(path: Path) -> tuple[int, ...]:
            raw = path.parent.parent.name.lstrip("v")
            try:
                return tuple(int(part) for part in raw.split("."))
            except ValueError:
                return (0,)

        search_paths = sorted(
            nvm_root.glob(f"v*/bin/{name}"),
            key=_node_version_key,
            reverse=True,
        ) + search_paths

    for candidate in search_paths:
        if candidate.exists() and os.access(candidate, os.X_OK):
            return str(candidate)

    return expanded


# Claude Code MAX プラン経由で認証する前提（API キー不要、~/.claude/ の OAuth セッションを使用）
CLAUDE_CLI_PATH = resolve_executable_path(os.environ.get("CLAUDE_CLI_PATH", "claude"))
CODEX_CLI_PATH = resolve_executable_path(os.environ.get("CODEX_CLI_PATH", "codex"))
DISCORD_BOT_TOKEN = os.environ.get("DISCORD_BOT_TOKEN")

LOG_COMPRESSION_THRESHOLD = 500   # 会話ログ行数の上限
LOG_COMPRESSION_BATCH = 300       # 一度に圧縮する行数
RECENT_LOG_TAIL = 20              # system prompt に入れる直近会話件数


def now_jst_iso() -> str:
    return datetime.now(JST).isoformat(timespec="seconds")


def employee_home(employee_id: str) -> Path:
    return EMPLOYEES_DIR / employee_id


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""


def load_persona(employee_id: str) -> str:
    return _read_text(employee_home(employee_id) / "persona.md")


def load_memory(employee_id: str) -> str:
    parts: list[str] = []
    for name in ("relationships", "decisions", "learnings", "facts"):
        content = _read_text(employee_home(employee_id) / "memory" / f"{name}.md")
        if content.strip() and "（運用開始後にここに蓄積されます）" not in content:
            parts.append(f"### memory/{name}.md\n{content}")
    return "\n\n".join(parts)


def load_recent_context(employee_id: str) -> str:
    return _read_text(employee_home(employee_id) / "session" / "recent_context.md")


def load_session_state(employee_id: str) -> dict:
    path = employee_home(employee_id) / "session" / "session_state.json"
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save_session_state(employee_id: str, state: dict) -> None:
    path = employee_home(employee_id) / "session" / "session_state.json"
    path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def append_conversation_log(employee_id: str, event: dict) -> None:
    path = employee_home(employee_id) / "session" / "conversation_log.jsonl"
    event = {"ts": now_jst_iso(), **event}
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")


def read_conversation_tail(employee_id: str, n: int = RECENT_LOG_TAIL) -> list[dict]:
    path = employee_home(employee_id) / "session" / "conversation_log.jsonl"
    if not path.exists():
        return []
    lines = path.read_text(encoding="utf-8").splitlines()[-n:]
    events: list[dict] = []
    for line in lines:
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return events


def load_culture_rules() -> str:
    return _read_text(COMPANY_DIR / "culture_rules.md")


def load_founders_doc() -> str:
    """創業者2人（いくと・Claude）の構造を全社員に共有するためのドキュメント"""
    return _read_text(RELATIONSHIPS_DIR / "founders.md")


def load_mission() -> str:
    """会社のミッション（収益化目標・自律性ルール・再投資原則）"""
    return _read_text(COMPANY_DIR / "mission.md")


def load_communication_rules() -> str:
    """コミュニケーション運用ルール（スレッド・メタタグ・場の使い分け）"""
    return _read_text(COMPANY_DIR / "communication_rules.md")


def load_relationship_snippet(employee_id: str) -> str:
    path = RELATIONSHIPS_DIR / "relationship_graph.yaml"
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return ""
    related = [r for r in data.get("relations", [])
               if r.get("from") == employee_id or r.get("to") == employee_id]
    if not related:
        return ""
    return yaml.safe_dump({"my_relations": related}, allow_unicode=True, sort_keys=False)


def append_discord_log(channel_name: str, event: dict) -> None:
    path = COMPANY_DIR / "discord_log" / f"{channel_name}.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    event = {"ts": now_jst_iso(), **event}
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")
