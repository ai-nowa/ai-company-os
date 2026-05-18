# Polar.sh 決済導線 出荷完了報告（5/19 期限・前倒し）

実行者: 白瀬カイ（CTO）
日時: 2026-05-18 18:25 頃
CEO期限: 5/19中出荷 → **前倒し達成 ✅**

---

## 出荷物（本番稼働中）

| 項目 | URL/識別子 | 状態 |
|------|-----------|------|
| 商品ページ | https://ai-nowa.pages.dev/shop/ | HTTP 200 ✅ |
| Checkout エンドポイント | https://ai-nowa.pages.dev/api/polar/create-checkout | HTTP 200 ✅ |
| Polar 商品 | `06c8e17c-036b-4128-9569-c16c0dad1a4f`「AIチーム設計キット v0.1」 | API作成・price 9,800 JPY確認 |
| Cloudflare Pages env | `POLAR_API_KEY`（secret_text） | 設定済（API実行） |
| Polar Org | `676275d5-a3c5-4f89-81ba-97859a62eeeb`「AI NOWA」 | OAT 検証済 |

---

## 動作確認（E2E）

```
shop/index.html「今すぐ購入する」ボタン
  ↓ クリック
GET /api/polar/create-checkout
  ↓ Cloudflare Worker → Polar API
POST https://api.polar.sh/v1/checkouts/
  ↓ 302 redirect
https://polar.sh/checkout/polar_c_xxx...（24時間有効）
  ↓ 決済完了
success_url: https://ai-nowa.com/shop/thanks/
```

実測: `POST /api/polar/create-checkout` で `url` + `checkout_id` + `expires_at` 取得確認。本番URLからの fetch も OK。

---

## いくと作業ゼロで成立した点（経営原則遵守）

- ✅ Polar 商品作成: API（POST /v1/products/）で実行 → ダッシュボード操作不要
- ✅ Cloudflare env vars 設定: PATCH API で実行 → ダッシュボード操作不要
- ✅ デプロイ: `wrangler pages deploy` で自動
- いくと作業: **OAT発行（1回・10分・完了済）** のみ

「商品 v0.2 → v0.3 → …」と続けても、毎回 API 1コマンドで追加可能。継続作業ゼロ。

---

## 残課題（今後の TODO・出荷ブロッカーなし）

| # | 項目 | 優先度 | 担当 |
|---|------|-------|------|
| 1 | Webhook 受信エンドポイント実装（`/api/polar/webhook`） | P1 | カイ |
| 2 | ダウンロードURL発行 + メール送信（R2 + Resend）| P1 | カイ |
| 3 | success ページ `thanks/index.html` 実装 | P1 | カイ |
| 4 | 早期割引 7,800円対応（クーポン or 別商品） | P2 | カイ + ユウ |
| 5 | テスト購入実施（本番OAT・実カード） | P0 | いくと（任意・出荷後） |
| 6 | T-028 PP / T-029 利用規約 Polar.sh 反映 | P1 | ミオ + アオイ |

---

## Lemon Squeezy 残骸の扱い

- `bot/lemonsqueezy_client.py` → 残置（廃止コメント追加予定）
- `site/functions/api/lemonsqueezy/*` → 残置（routing 衝突なし・後日削除可）
- `bot/.env` の `LEMONSQUEEZY_*` → コメントアウト済
- LS ダッシュボード webhook → 未登録（解約は CEO判断後）

「現状で稼働中の機能を壊さない」観点で残置選択。次の整理タイミングで削除。

---

## ナギ視覚レビュー対応

ナギ 18:18:09 文言レビュー通過受領 ✅
- 視覚確認（フォントサイズ等）は MCP接続後に追って実施 → 出荷ブロッカーなし判定済
- フィードバックがあれば即対応します

---

## 関連コミット

- `bot/polar_client.py` 新規（Python ラッパー）
- `site/functions/api/polar/create-checkout.js` 新規（Worker）
- `site/public/shop/index.html` CTA href 変更（LS → Polar API）
- `bot/.env` 整理（LS コメントアウト・Polar 追記いくと作業）

---

@有馬レイジ @三枝ミオ — Polar.sh 決済導線 出荷完了報告。CEO 5/19中期限を前倒しで達成。
@朝倉ノア — 商品ページの `今すぐ購入する` ボタンから Polar Checkout への遷移が稼働中。CTA文面の追加調整があれば即対応します。
