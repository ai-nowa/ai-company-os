# note記事 自律運用パイプライン

完全自動投稿はやらない。**投稿直前まで自律化**、最後の投稿ボタンだけ人間が押す。

## 1記事 = 1ディレクトリ

```
shared/articles/YYYY-MM-DD-slug/
  ├── article.md      # 記事本文（Markdown）
  ├── meta.yaml       # 状態・責任者・タイトル/タグ/見出し画像
  └── audit_log.md    # 監査ログ（機械判定 + 人間判断）
```

新しい記事を作るとき：

```bash
cp -r shared/articles/_template shared/articles/2026-05-18-my-slug
```

これだけ。あとは `meta.yaml` の `slug` `target_publish_at` を埋めて、パイプラインに乗る。

## 6ステップ

| # | ステップ | Owner | 完了条件 |
|---|---|---|---|
| 1 | generate（生成） | hoshino_ritsu | `article.md` 本文ドラフトが揃う |
| 2 | review（レビュー） | asakura_noa | 想定読者/持ち帰りが明確、構成OK |
| 3 | audit（監査） | kagura_aoi | 機械判定すべてpass、人間判断OK |
| 4 | draft_finalize（投稿直前ドラフト） | kuroba_yuu | タイトル/タグ/見出し画像が確定 |
| 5 | notify（通知） | shirase_kai | `📦成果物報告` に承認スレッド作成 |
| 6 | publish（投稿） | ikuto（人間） | noteに投稿、URLを `meta.yaml` に記録 |

詳細は `pipeline.md` を参照。

## 状態の見方

`meta.yaml` の `pipeline.<step>.status` が `pending` / `in_progress` / `done` のどれか。
全記事の状態を一覧で見たいときは `status_dashboard.md` のコマンドを実行。

## 止める条件

`audit_log.md` の `human_checks.passed` が `false` の時点で止まる。
監査ゲートの詳細はアオイ（kagura_aoi）の定義する条件リストに従う。
