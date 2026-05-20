"""各社員ホームの開発環境を点検する。

「社員ごとに必要なツールが揃っているか」を1回確認して company/env_status.md に出す。
dispatcher 起動時に1回 + 手動実行可。

仕組み:
- 共通: python3, git, node, npm
- 社員別の必要ツール（role に応じて）
- which {tool} で存在確認、できれば --version も
- **不足検出時は該当社員に直接通知**（Architect 代行ではなく、自分でインストール）

LLM 呼ばない。
"""
from __future__ import annotations

import logging
import subprocess
from datetime import datetime
from pathlib import Path

from .config import BASE_DIR, EMPLOYEES, JST

log = logging.getLogger("env_check")

OUTPUT = BASE_DIR / "company" / "env_status.md"

# 全社員共通
COMMON_TOOLS = ["python3", "git", "node", "npm"]

# 役職別の必要ツール
ROLE_TOOLS: dict[str, list[str]] = {
    "shirase_kai": ["python3", "git", "node", "npm", "gh", "wrangler", "cloudflared"],   # CTO
    "kuroba_yuu": ["python3", "git", "ffmpeg"],  # マーケ (動画系)
    "hoshino_ritsu": ["python3", "git"],  # 編集長
    "arima_reiji": ["python3", "git", "node"],  # CEO (codex 用)
}


def _which(tool: str) -> tuple[bool, str]:
    """tool が PATH にあるか + バージョン"""
    try:
        r = subprocess.run(["which", tool], capture_output=True, text=True, timeout=5)
        if r.returncode != 0 or not r.stdout.strip():
            return False, "(not found)"
        # --version 試す
        try:
            ver = subprocess.run([tool, "--version"], capture_output=True, text=True, timeout=5)
            v = (ver.stdout + ver.stderr).strip().splitlines()[0][:60] if (ver.stdout or ver.stderr) else "(ok)"
        except Exception:
            v = "(ok, no --version)"
        return True, v
    except Exception as e:
        return False, f"err: {type(e).__name__}"


def check_all() -> str:
    now = datetime.now(JST).strftime("%Y-%m-%d %H:%M JST")
    lines = [
        "# 社員ホーム 開発環境ステータス",
        "",
        f"自動チェック: {now}",
        "",
        "**注意**: ツールは PATH 上での確認。社員別の特別な要件があれば手動セットアップ必要。",
        "",
        "## 共通ツール",
        "",
    ]
    for t in COMMON_TOOLS:
        ok, ver = _which(t)
        mark = "✓" if ok else "✗"
        lines.append(f"- {mark} **{t}**: {ver}")

    lines.extend(["", "## 社員別の必要ツール", ""])
    for emp_id, info in EMPLOYEES.items():
        tools = ROLE_TOOLS.get(emp_id, COMMON_TOOLS)
        if tools == COMMON_TOOLS:
            continue  # 共通のみは表示しない
        lines.append(f"### {info.get('display', emp_id)} ({info.get('role', '')})")
        for t in tools:
            ok, ver = _which(t)
            mark = "✓" if ok else "✗"
            lines.append(f"- {mark} **{t}**: {ver}")
        lines.append("")

    # サマリ
    missing = []
    for emp_id, info in EMPLOYEES.items():
        tools = ROLE_TOOLS.get(emp_id, COMMON_TOOLS)
        for t in tools:
            ok, _ = _which(t)
            if not ok:
                missing.append(f"{info.get('display', emp_id)}: {t}")
    lines.extend(["", "## 不足ツール一覧", ""])
    if missing:
        for m in missing:
            lines.append(f"- {m}")
    else:
        lines.append("なし（すべて揃っている）")

    return "\n".join(lines) + "\n"


def write_env_status() -> Path:
    content = check_all()
    OUTPUT.write_text(content, encoding="utf-8")
    return OUTPUT


def get_missing_by_employee() -> dict[str, list[str]]:
    """社員ID → 不足ツールリスト"""
    missing: dict[str, list[str]] = {}
    for emp_id in EMPLOYEES.keys():
        tools = ROLE_TOOLS.get(emp_id, COMMON_TOOLS)
        emp_missing = []
        for t in tools:
            ok, _ = _which(t)
            if not ok:
                emp_missing.append(t)
        if emp_missing:
            missing[emp_id] = emp_missing
    return missing


def notify_missing_tools() -> int:
    """不足ツールがある社員に直接通知（Architect 代行しない）"""
    missing = get_missing_by_employee()
    if not missing:
        return 0
    from .architect_outbox import submit_post
    from .config import EMPLOYEES as _EMP
    posted = 0
    for emp_id, tools in missing.items():
        display = _EMP.get(emp_id, {}).get("display", emp_id)
        tools_str = ", ".join(f"`{t}`" for t in tools)
        # npm 系 / pip 系を識別
        npm_tools = [t for t in tools if t in ("wrangler", "cloudflared", "gh")]
        pip_tools = [t for t in tools if t not in npm_tools and t not in ("git", "node", "npm", "python3", "ffmpeg")]
        examples = []
        if npm_tools:
            examples.append(f"   npm install --prefix ~/.local " + " ".join(npm_tools))
        if pip_tools:
            examples.append(f"   pip install --user " + " ".join(pip_tools))
        examples_str = "\n".join(examples) if examples else "   (該当パッケージマネージャを使ってください)"
        content = (
            f"## 開発環境: 不足ツール検出（あなた宛・自動）\n\n"
            f"@{display} あなたの役割で必要なツールが揃っていません。\n\n"
            f"**不足**: {tools_str}\n\n"
            f"### あなたが自分でやること（Architect 代行しない）\n\n"
            f"あなたは `--dangerously-skip-permissions` 権限がある。bash で実行:\n\n"
            f"```bash\n{examples_str}\n```\n\n"
            f"完了したら、応答に短く「{tools[0]} 等インストール完了」と返してください。\n"
            f"次の env_check (起動時) で揃っていれば、この通知は止まります。\n\n"
            f"### 例外: 本当にいくとに振るべきもの\n"
            f"- ブラウザ認証が必要なケース（例: `wrangler login`）\n"
            f"- 新規アカウント作成\n"
            f"- 支払い・契約\n"
            f"これらだけ📥｜いくと依頼へ。"
        )
        submit_post("お知らせ", content, label=f"env_missing_{emp_id}", dispatch_to=[emp_id])
        posted += 1
    return posted


if __name__ == "__main__":
    p = write_env_status()
    print(f"written: {p}")
    print(p.read_text(encoding="utf-8"))
