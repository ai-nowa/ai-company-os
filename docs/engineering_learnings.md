# エンジニアリング learnings（再発防止メモ）

技術的インシデント・設定ミスの記録。次回同じ問題を踏まないための参照。

---

## L-001: ZENN_USERNAME はアンダースコア (2026-05-17)

**事象**: `zenn.dev/ai-nowa/articles/...` が 404 を返し続けた。

**原因**: `bot/zenn_publisher.py` の `ZENN_USERNAME` デフォルト値が `ai-nowa`（ハイフン）で誤設定。Zenn アカウントの実際のユーザー名は `ai_nowa`（アンダースコア）。

**背景**: Zenn のスラッグ仕様（ハイフン推奨・アンダースコア非推奨）を、ユーザー名にも適用してしまったため。ユーザー名とスラッグは別物。

**修正**: `e7cf0a5` — デフォルト値を `"ai_nowa"` に変更。

**チェックルール**: 外部サービスの username を設定値に入れる前に `curl -o /dev/null -w "%{http_code}" https://{service}/{username}` で実 URL を確認する。

---

## L-002: Zenn スラッグにアンダースコア不可 (2026-05-17)

**事象**: `_SLUG_RE` がアンダースコアを許可していたが、Zenn の実仕様では slug にアンダースコアは非推奨。

**修正**: `befde0d` — `_SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]{10,48}[a-z0-9]$")`

**チェックルール**: Zenn スラッグは英小文字・数字・ハイフンのみ。ユーザー名（アンダースコア可）とスラッグ（アンダースコア不可）で文字セットが異なる。

---

## L-003: `git commit` は "nothing to commit" を想定して冪等化する (2026-05-17)

**事象**: `published: true` が既に push 済みの状態で publisher を再実行すると、`git commit` が rc=1 で終了してスクリプト全体がエラー落ちした。

**修正**: `1cc3481` — `git diff --cached --quiet` で staged 変更がない場合はコミットをスキップ。

**チェックルール**: git 操作を含む自動化スクリプトでは「変更なし」ケースを必ず処理する。`subprocess.run(..., check=True)` を使う前に、操作が冪等かを確認。
