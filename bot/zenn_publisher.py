"""Zenn 記事の監査済み公開スクリプト。

監査 lockファイルが存在し、5 Gate を全て通過した時のみ
articles/{slug}.md の published: false → true を変更し、
git commit + gh push を実行する。

サイレント失敗禁止: 成功・失敗いずれも Discord 通知必須。

使い方:
    python -m bot.zenn_publisher <slug>
    例: python -m bot.zenn_publisher ai-nowa-design-record-v01
"""
from __future__ import annotations

import hashlib
import logging
import os
import re
import subprocess
import sys
from pathlib import Path

import yaml

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("zenn_publisher")

REPO_ROOT = Path(os.environ.get("COMPANY_BASE_DIR", "/home/ikuto/ai-company-os"))
AUDIT_CLEARANCE_DIR = REPO_ROOT / "employees" / "kagura_aoi" / "outbox" / "audit_clearance"
ARTICLES_DIR = REPO_ROOT / "articles"
ZENN_USERNAME = os.environ.get("ZENN_USERNAME", "ai-nowa")

# Zenn slug の形式: 英小文字・数字・ハイフンのみ、12〜50文字、先頭末尾は英数字
# アンダースコアは Zenn の実仕様では非推奨のため除外
_SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]{10,48}[a-z0-9]$")


# ── カスタム例外 ──────────────────────────────────────────────────────────────

class AuditNotClearedError(Exception):
    pass


class AuditTamperedError(Exception):
    pass


class AuditConditionsPendingError(Exception):
    pass


class PublishError(Exception):
    pass


class InvalidSlugError(Exception):
    pass


# ── Discord 通知（webhook ベース / なければログ警告） ──────────────────────────

def _alert_discord(message: str) -> None:
    """サイレント失敗禁止: 通知失敗でも例外は raise しない（ログに残す）。"""
    webhook_url = os.environ.get("DISCORD_WEBHOOK_URL")
    if not webhook_url:
        log.warning("[DISCORD_ALERT] (webhook未設定) %s", message)
        return
    try:
        import urllib.request
        import json as _json
        payload = _json.dumps({"content": message}).encode()
        req = urllib.request.Request(
            webhook_url,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=10):
            pass
    except Exception as exc:
        log.error("[DISCORD_ALERT FAILED] %s / reason: %s", message, exc)


# ── 内部ユーティリティ ─────────────────────────────────────────────────────────

def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _set_published_true(article_path: Path) -> None:
    """frontmatter の published: false を published: true に書き換える。

    この関数は 5 Gate を全て通過した後にのみ呼ばれる。
    外部から直接呼ばれないよう _ プレフィックスで private 扱い。
    """
    content = article_path.read_text(encoding="utf-8")
    updated = re.sub(
        r"^(published:\s*)false\s*$",
        r"\1true",
        content,
        flags=re.MULTILINE,
    )
    if updated == content:
        # すでに true の場合はスキップ（冪等性確保）
        log.info("published: already true, skip rewrite")
        return
    article_path.write_text(updated, encoding="utf-8")
    log.info("published: false → true: %s", article_path)


def _git_commit_and_push(article_path: Path, slug: str) -> None:
    """記事ファイルと lockファイルをコミットして push する。"""
    lock_path = AUDIT_CLEARANCE_DIR / f"{slug}.lock"
    files = [str(article_path.relative_to(REPO_ROOT)), str(lock_path.relative_to(REPO_ROOT))]
    subprocess.run(
        ["git", "-C", str(REPO_ROOT), "add"] + files,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "-C", str(REPO_ROOT), "commit", "-m",
         f"publish: Zenn公開 — {slug} [audit_cleared]"],
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "-C", str(REPO_ROOT), "push", "origin", "main"],
        check=True,
        capture_output=True,
    )
    log.info("push complete: %s", slug)


def _validate_slug(slug: str) -> None:
    """Gate 0: slug 形式チェック（純粋な文字列検証のみ、ファイルに触らない）。

    記事ファイルの存在確認は Gate 3（publish_to_zenn 内）で行う。
    """
    if not isinstance(slug, str) or not slug.strip():
        raise InvalidSlugError("slug は空にできません")
    if not _SLUG_RE.match(slug):
        raise InvalidSlugError(
            f"不正な slug: {slug!r} — "
            "英小文字・数字・ハイフン・アンダースコアのみ、12〜50文字、先頭末尾は英数字"
        )


def _check_notes_no_secrets(notes: str) -> None:
    """notes フィールドに機密情報が混入していないか簡易チェック。

    Public リポジトリに載るため、明らかな秘密情報パターンを弾く。
    """
    danger_patterns = [
        r"sk-ant-[A-Za-z0-9_-]{10,}",              # Anthropic key
        r"sk-[A-Za-z0-9]{20,}",                    # OpenAI key
        r"gh[ps]_[A-Za-z0-9]{10,}",                # GitHub PAT
        r"-----BEGIN .*PRIVATE KEY-----",            # PEM 秘密鍵
        r"note_session_v5[=:]\s*\S{10,}",           # note session cookie
        r"AGE-SECRET-KEY-1[A-Z0-9]{20,}",           # age secret key
        r"[MN][A-Za-z\d]{23}\.[A-Za-z\d_-]{6}\.[A-Za-z\d_-]{27}",  # Discord bot token
    ]
    for pat in danger_patterns:
        if re.search(pat, notes or "", flags=re.IGNORECASE):
            raise AuditTamperedError(
                f"notes フィールドに機密情報パターンが検出されました。lockファイルを確認してください。"
            )


# ── メイン: 5 Gate ────────────────────────────────────────────────────────────

def publish_to_zenn(slug: str) -> str:
    """
    5 Gate を全て通過した時のみ published: true に変更して push する。

    Gate 1: lockファイル存在確認
    Gate 2: verdict == "ok" 確認
    Gate 3: article_sha256 一致確認（監査後改ざん検知）
    Gate 4: conditions 未対応項目なし確認
    Gate 5: notes フィールドに機密情報がないこと確認
    ────────────── ここまで通過した時のみ ──────────────
    _set_published_true → _git_commit_and_push → Discord 通知
    """
    article_path = ARTICLES_DIR / f"{slug}.md"
    lock_path = AUDIT_CLEARANCE_DIR / f"{slug}.lock"
    zenn_url = f"https://zenn.dev/{ZENN_USERNAME}/articles/{slug}"

    try:
        # Gate 0: slug バリデーション（不正 slug を保存前に停止）
        _validate_slug(slug)

        # Gate 1: lockファイル存在確認
        if not lock_path.exists():
            raise AuditNotClearedError(
                f"Gate 1 FAIL: lockファイルが存在しません: {lock_path}"
            )

        # lockファイルをパース
        lock = yaml.safe_load(lock_path.read_text(encoding="utf-8")) or {}

        # Gate 2: verdict == "ok" 確認（大文字小文字を正規化）
        verdict = str(lock.get("verdict", "")).strip().lower()
        if verdict != "ok":
            raise AuditNotClearedError(
                f"Gate 2 FAIL: verdict={lock.get('verdict')!r} (expected 'ok')"
            )

        # Gate 3: article_sha256 一致確認
        if not article_path.exists():
            raise PublishError(f"Gate 3 FAIL: 記事ファイルが存在しません: {article_path}")
        expected_hash = str(lock.get("article_sha256", "")).strip().lower()
        current_hash = _sha256_file(article_path)
        if not expected_hash:
            raise AuditTamperedError("Gate 3 FAIL: lockファイルに article_sha256 がありません")
        if expected_hash != current_hash:
            raise AuditTamperedError(
                f"Gate 3 FAIL: SHA-256 不一致 — 監査後に記事が変更されています\n"
                f"  lock: {expected_hash}\n"
                f"  now:  {current_hash}"
            )

        # Gate 4: conditions 未対応項目なし確認
        conditions = lock.get("conditions") or []
        pending = [c for c in conditions if str(c).strip()]
        if pending:
            raise AuditConditionsPendingError(
                f"Gate 4 FAIL: conditions に未対応項目があります: {pending}"
            )

        # Gate 5: notes フィールドの機密混入防止チェック
        _check_notes_no_secrets(str(lock.get("notes", "") or ""))

        # ── 全 Gate 通過 ─────────────────────────────────────────────────
        log.info("All gates passed. Publishing %s ...", slug)
        _set_published_true(article_path)
        _git_commit_and_push(article_path, slug)

        success_msg = (
            f"✅ Zenn公開完了: {slug}\n"
            f"URL: {zenn_url}\n"
            f"審査: {lock.get('auditor', 'kagura_aoi')} / {lock.get('audited_at', '')}"
        )
        log.info(success_msg)
        _alert_discord(success_msg)
        return zenn_url

    except (InvalidSlugError, AuditNotClearedError, AuditTamperedError, AuditConditionsPendingError, PublishError) as exc:
        error_msg = f"🚫 Zenn公開停止: {slug}\n理由: {exc}"
        log.error(error_msg)
        _alert_discord(error_msg)
        raise
    except Exception as exc:
        error_msg = f"🚨 Zenn公開 予期しないエラー: {slug}\n{type(exc).__name__}: {exc}"
        log.error(error_msg)
        _alert_discord(error_msg)
        raise


# ── CLI エントリーポイント ─────────────────────────────────────────────────────

def main() -> None:
    if len(sys.argv) < 2:
        print(f"使い方: python -m bot.zenn_publisher <slug>", file=sys.stderr)
        sys.exit(1)
    slug = sys.argv[1]
    try:
        url = publish_to_zenn(slug)
        print(f"公開完了: {url}")
    except Exception:
        sys.exit(1)


if __name__ == "__main__":
    main()
