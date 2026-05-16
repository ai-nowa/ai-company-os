"""bot/zenn_publisher.py のテスト。

仕様:
- Gate 0: slug バリデーション（不正 slug を保存前に止める）
- Gate 1-5: 監査 lock + SHA-256 + conditions + notes 機密スキャン
- articles/ 既存ファイルは正常系以外で書き換えない
"""
from __future__ import annotations

import hashlib
import textwrap
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import yaml

import bot.zenn_publisher as zp
from bot.zenn_publisher import (
    AuditConditionsPendingError,
    AuditNotClearedError,
    AuditTamperedError,
    InvalidSlugError,
    _validate_slug,
    publish_to_zenn,
)


# ── ヘルパー ──────────────────────────────────────────────────────────────────

VALID_SLUG = "ai-nowa-design-record-v01"  # 26文字、実在する slug

ARTICLE_BODY = textwrap.dedent("""\
    ---
    title: "テスト記事"
    published: false
    ---

    本文。
""")


def _make_article(articles_dir: Path, slug: str, body: str = ARTICLE_BODY) -> Path:
    path = articles_dir / f"{slug}.md"
    path.write_text(body, encoding="utf-8")
    return path


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _make_lock(lock_dir: Path, slug: str, article_path: Path, **overrides) -> Path:
    lock_dir.mkdir(parents=True, exist_ok=True)
    data = {
        "slug": slug,
        "article_path": f"articles/{slug}.md",
        "article_sha256": _sha256(article_path),
        "audited_at": "2026-05-16T23:00:00+09:00",
        "auditor": "kagura_aoi",
        "verdict": "ok",
        "conditions": [],
        "notes": "",
    }
    data.update(overrides)
    path = lock_dir / f"{slug}.lock"
    path.write_text(yaml.dump(data, allow_unicode=True), encoding="utf-8")
    return path


# ── Gate 0: slug バリデーション ───────────────────────────────────────────────

class TestValidateSlug:
    def test_valid_slug_passes(self, tmp_path):
        slug = "ai-nowa-design-record-v01"
        (tmp_path / f"{slug}.md").write_text("x")
        with patch.object(zp, "ARTICLES_DIR", tmp_path):
            _validate_slug(slug)  # 例外なし

    @pytest.mark.parametrize("bad_slug", [
        "",                   # 空
        "short",              # 5文字（12文字未満）
        "-starts-with-hyphen-ok",    # 先頭ハイフン
        "UPPER-CASE-SLUG-HERE-01",   # 大文字
        "has space in slug ok here",  # スペース
        "a" * 51,             # 51文字（50文字超）
        "../etc/passwd-hoge",  # パストラバーサル
    ])
    def test_invalid_format_raises(self, bad_slug):
        with pytest.raises(InvalidSlugError):
            _validate_slug(bad_slug)

    def test_missing_article_file_raises(self, tmp_path):
        with patch.object(zp, "ARTICLES_DIR", tmp_path):
            with pytest.raises(InvalidSlugError, match="が存在しません"):
                _validate_slug(VALID_SLUG)

    def test_existing_articles_not_modified(self, tmp_path):
        """バリデーション中は articles/ 内の他ファイルに触れない。"""
        other = tmp_path / "other-existing-article-v01.md"
        other.write_text("original content", encoding="utf-8")
        target = tmp_path / f"{VALID_SLUG}.md"
        target.write_text("x")
        with patch.object(zp, "ARTICLES_DIR", tmp_path):
            _validate_slug(VALID_SLUG)
        assert other.read_text() == "original content"


# ── Gate 1-5 + publish_to_zenn ───────────────────────────────────────────────

@pytest.fixture()
def env(tmp_path):
    """articles/ と audit_clearance/ を tmp_path 配下に差し替えた環境。"""
    articles_dir = tmp_path / "articles"
    articles_dir.mkdir()
    lock_dir = tmp_path / "audit_clearance"

    article_path = _make_article(articles_dir, VALID_SLUG)

    with (
        patch.object(zp, "ARTICLES_DIR", articles_dir),
        patch.object(zp, "AUDIT_CLEARANCE_DIR", lock_dir),
        patch("bot.zenn_publisher._git_commit_and_push"),
        patch("bot.zenn_publisher._alert_discord"),
    ):
        yield {
            "articles_dir": articles_dir,
            "lock_dir": lock_dir,
            "article_path": article_path,
        }


class TestPublishToZenn:
    def test_normal_publish_sets_published_true(self, env):
        _make_lock(env["lock_dir"], VALID_SLUG, env["article_path"])
        url = publish_to_zenn(VALID_SLUG)
        assert url.startswith("https://zenn.dev/")
        content = env["article_path"].read_text(encoding="utf-8")
        assert "published: true" in content
        assert "published: false" not in content

    def test_gate1_no_lock_file(self, env):
        with pytest.raises(AuditNotClearedError, match="Gate 1"):
            publish_to_zenn(VALID_SLUG)
        # articles/ は書き換えられていない
        assert "published: false" in env["article_path"].read_text()

    def test_gate2_verdict_not_ok(self, env):
        _make_lock(env["lock_dir"], VALID_SLUG, env["article_path"], verdict="revoked")
        with pytest.raises(AuditNotClearedError, match="Gate 2"):
            publish_to_zenn(VALID_SLUG)
        assert "published: false" in env["article_path"].read_text()

    def test_gate2_verdict_case_insensitive_ok(self, env):
        _make_lock(env["lock_dir"], VALID_SLUG, env["article_path"], verdict="OK")
        url = publish_to_zenn(VALID_SLUG)
        assert url.startswith("https://zenn.dev/")

    def test_gate3_sha256_mismatch(self, env):
        _make_lock(env["lock_dir"], VALID_SLUG, env["article_path"],
                   article_sha256="deadbeef" * 8)
        with pytest.raises(AuditTamperedError, match="Gate 3"):
            publish_to_zenn(VALID_SLUG)
        assert "published: false" in env["article_path"].read_text()

    def test_gate4_pending_conditions(self, env):
        _make_lock(env["lock_dir"], VALID_SLUG, env["article_path"],
                   conditions=["センシティブ表現の修正が必要"])
        with pytest.raises(AuditConditionsPendingError, match="Gate 4"):
            publish_to_zenn(VALID_SLUG)
        assert "published: false" in env["article_path"].read_text()

    def test_gate5_notes_with_secret(self, env):
        _make_lock(env["lock_dir"], VALID_SLUG, env["article_path"],
                   notes="sk-ant-api03-supersecretkey12345678")
        with pytest.raises(AuditTamperedError):
            publish_to_zenn(VALID_SLUG)
        assert "published: false" in env["article_path"].read_text()

    def test_discord_notified_on_failure(self, env):
        with patch("bot.zenn_publisher._alert_discord") as mock_alert:
            with pytest.raises(AuditNotClearedError):
                publish_to_zenn(VALID_SLUG)
            mock_alert.assert_called_once()
            assert "停止" in mock_alert.call_args[0][0]

    def test_discord_notified_on_success(self, env):
        _make_lock(env["lock_dir"], VALID_SLUG, env["article_path"])
        with patch("bot.zenn_publisher._alert_discord") as mock_alert:
            publish_to_zenn(VALID_SLUG)
            mock_alert.assert_called_once()
            assert "公開完了" in mock_alert.call_args[0][0]

    def test_existing_other_articles_untouched(self, env):
        """正常系でも他の記事ファイルは書き換えない。"""
        other = env["articles_dir"] / "other-article-slug-here.md"
        other.write_text("---\npublished: false\n---\n本文", encoding="utf-8")
        _make_lock(env["lock_dir"], VALID_SLUG, env["article_path"])
        publish_to_zenn(VALID_SLUG)
        assert "published: false" in other.read_text()
