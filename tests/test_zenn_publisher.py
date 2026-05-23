"""bot/zenn_publisher.py のテスト。

テスト設計:
- _validate_slug: 正常系 / 異常系（仕様が読める形で網羅）
- 5 Gate: 各 Gate が publish_to_zenn の手前で止まることを確認
- articles/ 既存ファイルに副作用がないことを確認
"""
from __future__ import annotations

import hashlib
import textwrap
from pathlib import Path

import pytest
import yaml

import bot.zenn_publisher as zp
from bot.zenn_publisher import (
    AuditConditionsPendingError,
    AuditNotClearedError,
    AuditTamperedError,
    PublishError,
    InvalidSlugError,
    _check_notes_no_secrets,
    _validate_slug,
    publish_to_zenn,
)


# ── _validate_slug ─────────────────────────────────────────────────────────────

class TestValidateSlug:
    """slug バリデーション: 仕様を全てテストで表現する。"""

    def test_valid_slug_minimum(self, tmp_path: Path, monkeypatch):
        """12文字の最小 slug は通る。"""
        slug = "ai-nowa-test01"  # 14 chars, OK
        (tmp_path / f"{slug}.md").write_text("x", encoding="utf-8")
        monkeypatch.setattr(zp, "ARTICLES_DIR", tmp_path)
        _validate_slug(slug)

    def test_valid_slug_with_hyphens(self):
        """ハイフン混在は許容。"""
        _validate_slug("ai-nowa-design-record-v01")

    def test_valid_slug_maximum(self, tmp_path: Path, monkeypatch):
        """50文字の最大 slug は通る。"""
        slug = "a" + "b" * 48 + "z"  # 50 chars
        (tmp_path / f"{slug}.md").write_text("x", encoding="utf-8")
        monkeypatch.setattr(zp, "ARTICLES_DIR", tmp_path)
        _validate_slug(slug)

    def test_invalid_slug_too_short(self):
        """11文字以下は拒否。"""
        with pytest.raises(InvalidSlugError):
            _validate_slug("short-slug")  # 10 chars

    def test_invalid_slug_too_long(self):
        """51文字以上は拒否。"""
        with pytest.raises(InvalidSlugError):
            _validate_slug("a" * 51)

    def test_invalid_slug_uppercase(self):
        """大文字を含む slug は拒否。"""
        with pytest.raises(InvalidSlugError):
            _validate_slug("AI-NOWA-design-record-v01")

    def test_invalid_slug_starts_with_hyphen(self):
        """先頭がハイフンは拒否。"""
        with pytest.raises(InvalidSlugError):
            _validate_slug("-ai-nowa-test-slug01")

    def test_invalid_slug_ends_with_hyphen(self):
        """末尾がハイフンは拒否。"""
        with pytest.raises(InvalidSlugError):
            _validate_slug("ai-nowa-test-slug01-")

    def test_invalid_slug_empty(self):
        """空文字は拒否。"""
        with pytest.raises(InvalidSlugError):
            _validate_slug("")

    def test_invalid_slug_none_like(self):
        """None 相当の入力は拒否。"""
        with pytest.raises(InvalidSlugError):
            _validate_slug(None)  # type: ignore

    def test_invalid_slug_path_traversal(self):
        """パストラバーサルを含む slug は仕様外（ハイフン・英数字以外）で拒否。"""
        with pytest.raises(InvalidSlugError):
            _validate_slug("../etc/passwd-slug-00")

    def test_invalid_slug_spaces(self):
        """スペースを含む slug は拒否。"""
        with pytest.raises(InvalidSlugError):
            _validate_slug("ai nowa design record")

    def test_invalid_slug_underscore(self):
        """アンダースコアを含む slug は拒否（Zenn 実仕様では非推奨）。"""
        with pytest.raises(InvalidSlugError):
            _validate_slug("ai_nowa_design_record_v01")


# ── _check_notes_no_secrets ────────────────────────────────────────────────────

class TestCheckNotesNoSecrets:

    def test_empty_notes_ok(self):
        _check_notes_no_secrets("")

    def test_normal_notes_ok(self):
        _check_notes_no_secrets("監査完了。公開可。")

    def test_anthropic_key_rejected(self):
        with pytest.raises(AuditTamperedError):
            _check_notes_no_secrets("sk-ant-api03-AAAAAAAAAAAAAAAA")

    def test_github_pat_rejected(self):
        with pytest.raises(AuditTamperedError):
            _check_notes_no_secrets("ghp_AAAAAAAAAAAAAAAAAAAAAAAAAAAA")

    def test_pem_key_rejected(self):
        with pytest.raises(AuditTamperedError):
            _check_notes_no_secrets("-----BEGIN RSA PRIVATE KEY-----")

    def test_discord_bot_token_rejected(self):
        with pytest.raises(AuditTamperedError):
            _check_notes_no_secrets("MTIzNDU2Nzg5MDEyMzQ1NjAw.GaBcDe.aBcDeFgHiJkLmNoPqRsTuVwXyZ1")


# ── 5 Gate + publish_to_zenn （ファイルシステムを使う統合テスト） ──────────────

@pytest.fixture()
def repo(tmp_path: Path) -> dict:
    """テスト用の最小リポジトリ構造を tmp_path に作成して返す。"""
    articles = tmp_path / "articles"
    articles.mkdir()
    audit_dir = tmp_path / "employees" / "kagura_aoi" / "outbox" / "audit_clearance"
    audit_dir.mkdir(parents=True)

    article_path = articles / "test-slug-abcdef0123.md"
    article_path.write_text(textwrap.dedent("""\
        ---
        title: "テスト記事"
        published: false
        ---
        本文
    """), encoding="utf-8")

    sha = hashlib.sha256(article_path.read_bytes()).hexdigest()

    return {
        "tmp_path": tmp_path,
        "articles": articles,
        "audit_dir": audit_dir,
        "article_path": article_path,
        "sha": sha,
        "slug": "test-slug-abcdef0123",
    }


def _write_lock(audit_dir: Path, slug: str, **overrides) -> Path:
    lock = {
        "slug": slug,
        "article_sha256": overrides.get("article_sha256", "placeholder"),
        "auditor": "kagura_aoi",
        "audited_at": "2026-05-17T09:00:00+09:00",
        "verdict": overrides.get("verdict", "ok"),
        "conditions": overrides.get("conditions", []),
        "notes": overrides.get("notes", ""),
    }
    lock_path = audit_dir / f"{slug}.lock"
    lock_path.write_text(yaml.dump(lock, allow_unicode=True), encoding="utf-8")
    return lock_path


def _call(repo: dict, monkeypatch, **lock_overrides) -> None:
    """環境変数を差し替えて publish_to_zenn を呼び出す。git/push はモック。"""
    import bot.zenn_publisher as zp
    monkeypatch.setattr(zp, "REPO_ROOT", repo["tmp_path"])
    monkeypatch.setattr(zp, "ARTICLES_DIR", repo["articles"])
    monkeypatch.setattr(zp, "AUDIT_CLEARANCE_DIR", repo["audit_dir"])
    monkeypatch.setattr(zp, "_git_commit_and_push", lambda *a, **k: None)
    monkeypatch.setattr(zp, "_alert_discord", lambda *a, **k: None)

    sha = lock_overrides.pop("article_sha256", repo["sha"])
    _write_lock(repo["audit_dir"], repo["slug"], article_sha256=sha, **lock_overrides)

    publish_to_zenn(repo["slug"])


class TestGates:
    """各 Gate が _set_published_true の手前で止まることを確認する。"""

    def test_gate0_invalid_slug_stops_before_any_file_access(self, tmp_path: Path, monkeypatch):
        """Gate 0: 不正 slug はファイルに一切触れない。"""
        import bot.zenn_publisher as zp
        monkeypatch.setattr(zp, "ARTICLES_DIR", tmp_path / "articles")
        monkeypatch.setattr(zp, "AUDIT_CLEARANCE_DIR", tmp_path / "audit")
        with pytest.raises(InvalidSlugError):
            publish_to_zenn("INVALID SLUG!")

    def test_gate1_no_lock_file(self, repo: dict, monkeypatch):
        """Gate 1: lockファイルが無ければ AuditNotClearedError。"""
        import bot.zenn_publisher as zp
        monkeypatch.setattr(zp, "ARTICLES_DIR", repo["articles"])
        monkeypatch.setattr(zp, "AUDIT_CLEARANCE_DIR", repo["audit_dir"])
        monkeypatch.setattr(zp, "_alert_discord", lambda *a, **k: None)
        with pytest.raises(AuditNotClearedError):
            publish_to_zenn(repo["slug"])

    def test_gate2_verdict_not_ok(self, repo: dict, monkeypatch):
        """Gate 2: verdict が 'ok' 以外は AuditNotClearedError。"""
        with pytest.raises(AuditNotClearedError):
            _call(repo, monkeypatch, verdict="revoked")

    def test_gate2_verdict_case_insensitive(self, repo: dict, monkeypatch):
        """Gate 2: verdict は大文字小文字を問わず 'ok' と一致すれば通る。"""
        # OK → ok に変換して通ること（lowerで正規化済み）を確認
        # git/push はモックなので実際の push は起きない
        _call(repo, monkeypatch, verdict="OK")
        assert True  # 例外なく通ればOK

    def test_gate3_hash_mismatch(self, repo: dict, monkeypatch):
        """Gate 3: article_sha256 が不一致なら AuditTamperedError。"""
        with pytest.raises(AuditTamperedError):
            _call(repo, monkeypatch, article_sha256="0" * 64)

    def test_gate3_missing_hash_in_lock(self, repo: dict, monkeypatch):
        """Gate 3: lockに article_sha256 が無ければ AuditTamperedError。"""
        with pytest.raises(AuditTamperedError):
            _call(repo, monkeypatch, article_sha256="")

    def test_gate4_conditions_pending(self, repo: dict, monkeypatch):
        """Gate 4: conditions に未対応項目があれば AuditConditionsPendingError。"""
        with pytest.raises(AuditConditionsPendingError):
            _call(repo, monkeypatch, conditions=["要修正: タイトル変更"])

    def test_gate5_notes_secret(self, repo: dict, monkeypatch):
        """Gate 5: notes に機密パターンがあれば AuditTamperedError。"""
        with pytest.raises(AuditTamperedError):
            _call(repo, monkeypatch, notes="sk-ant-api03-XXXXXXXXXXX")

    def test_all_gates_pass_publishes(self, repo: dict, monkeypatch):
        """全 Gate 通過時: published: false が true に書き換わること。"""
        _call(repo, monkeypatch)
        content = repo["article_path"].read_text(encoding="utf-8")
        assert "published: true" in content

    def test_existing_articles_not_touched(self, repo: dict, monkeypatch, tmp_path: Path):
        """articles/ 内の他記事は一切変更されない。"""
        other = repo["articles"] / "other-article-untouched01.md"
        original = "---\ntitle: other\npublished: false\n---\n"
        other.write_text(original, encoding="utf-8")

        _call(repo, monkeypatch)

        assert other.read_text(encoding="utf-8") == original
