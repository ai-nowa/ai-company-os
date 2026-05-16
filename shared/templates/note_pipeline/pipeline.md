# 6ステップ仕様

各ステップは「入力」「Owner」「やること」「出力」「完了トリガ」を持つ。
状態は `meta.yaml` の `pipeline.<step>.status` に書く（`pending` → `in_progress` → `done`）。

## 1. generate（生成）

- **Owner**: hoshino_ritsu（編集長）
- **入力**: 企画メモ（💡｜ひらめきメモ または 🎬｜youtube編集部 から拾う）
- **やること**: `article.md` を埋める。冒頭の「想定読者」「持ち帰り」も自分で埋める
- **出力**: `article.md`（ドラフト）
- **完了トリガ**: ステップ1を `done` に。ステップ2を `pending` で起動。`@asakura_noa` に投稿

## 2. review（レビュー）

- **Owner**: asakura_noa（PM）
- **入力**: `article.md`
- **やること**: 「想定読者」「持ち帰り」が明確か、構成に削れる/足すべき部分はないか
- **出力**: コメント（差分提案 or OK判定）。差し戻しの場合はステップ1に戻す
- **完了トリガ**: ステップ2を `done` に。`@kagura_aoi` に投稿

## 3. audit（監査）

- **Owner**: kagura_aoi（監査）
- **入力**: `article.md`
- **やること**: `audit_log.md` のチェックを実行。機械条件は自動、人間条件は自分で判定
- **出力**: `audit_log.md`（passed: true/false）
- **完了トリガ**: passed=true なら `done` でステップ4へ。false なら止める。`@kuroba_yuu`（pass時）または起案者（fail時）に投稿

## 4. draft_finalize（投稿直前ドラフト）

- **Owner**: kuroba_yuu（マーケ）
- **入力**: `article.md`, `meta.yaml`
- **やること**: タイトル、タグ、見出し画像の指示を `meta.yaml.meta` に確定
- **出力**: `meta.yaml`（タイトル/タグ/見出し画像が埋まった状態）
- **完了トリガ**: `done` でステップ5へ。`@shirase_kai` に投稿

## 5. notify（通知）

- **Owner**: shirase_kai（CTO）
- **入力**: 上記すべて
- **やること**: `📦成果物報告` チャンネルに承認スレッドを作成（記事プレビュー + メタ + 監査ログを貼る）
- **出力**: Discord承認スレッドURL（`meta.yaml.notes` に記録）
- **完了トリガ**: `done` でステップ6へ。`@ikuto`（人間）に通知

## 6. publish（投稿）

- **Owner**: ikuto（人間 Co-Founder）
- **入力**: ドラフト一式
- **やること**: noteにログイン → 記事を貼り付け → 見出し画像をセット → 投稿ボタン
- **出力**: noteのURL（`meta.yaml.published_url` に記録）
- **完了トリガ**: `done`。完了報告を `📦成果物報告` に。

## 進行中の止め方

どのステップでも `meta.yaml.pipeline.<step>.status` を `blocked` にして、`notes` に理由を書けば止まる。
ステップ3で `audit_log.md` の `passed: false` が出た時点でも自動的に止まる。
