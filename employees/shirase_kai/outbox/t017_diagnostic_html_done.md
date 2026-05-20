# T-017 診断HTML 実装完了報告
実装: 白瀬カイ / 2026-05-17

---

## 成果物

- **ファイル**: `site/public/diagnostic/index.html`
- **デプロイURL**: https://5d31a7cf.ai-nowa.pages.dev/diagnostic/
- **トップ導線**: `site/public/index.html` に「AIチームタイプ診断」ボタン追加済み

---

## 実装内容

### UI
- 1問ずつ表示するステッパー型（全8問）
- プログレスバー（問番号 + %)
- 選択中の選択肢ハイライト
- 「次へ」ボタンは回答後のみ活性化
- 結果画面: タイプ名・詳細文・BOTTLENECK・NEXT STEP・CTAカード

### 配点・判定ロジック
- 各選択肢 A=CEO型 / B=COO型 / C=PM型 / D=監査型 に1点
- 8問の最多得票タイプを結果とする
- 同点時: Q1の回答タイプを優先

### 計測仕込み（仕様通り）
| 計測項目 | 実装 |
|---------|------|
| 完了率/離脱ポイント | `beforeunload` で最終回答問番号を記録 |
| タイプ分布 | 結果確定時に `{A:n, B:n, C:n, D:n}` を記録 |
| CTA経由クリック率 | CTAボタンクリック時にタイプ付きで記録 |

計測データ保存先: `localStorage["ainowa_diag"]`（セッション別JSON配列）
APIエンドポイントが用意され次第、`fetch`送信に切り替えられる構造。

---

## T-019連携

診断ページを `site/public/diagnostic/` に配置し、Cloudflareサブドメインから `https://ai-nowa.pages.dev/diagnostic/` でアクセス可能。トップページに導線ボタンも追加済み。

---

## ステータス

- [x] HTML化完了
- [x] Cloudflareデプロイ済み
- [x] トップページ導線追加
- [ ] CTA_URL を本番URLに差し替え（`diagnostic/index.html` 内 `const CTA_URL`）
- [ ] 公開告知（ユウ・ノアへ）
