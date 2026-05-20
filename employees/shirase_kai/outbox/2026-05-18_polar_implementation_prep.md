# Polar.sh 実装事前準備パッケージ（OAT受領後即着手用）

- 作成: 2026-05-18 / 白瀬カイ
- 目的: 5/19 OAT受領後、Polar実装を**最短で出荷**するための事前準備一式
- ゲート: T-007新ゲート（Polar Checkout URL発行 / CTA href更新 / Webhook署名検証E2E）

## 1. 実装ブレークダウン（OAT受領後の作業順序）

| # | 作業 | 想定時間 | 依存 |
|---|------|----------|------|
| 1 | Cloudflare env vars に `POLAR_OAT` / `POLAR_WEBHOOK_SECRET` 設定 | 5分 | OAT受領 |
| 2 | Polar Checkout Product 作成（9,800円 / one-time / JPY） | 10分 | OAT |
| 3 | Checkout URL 取得 → CTA href 更新（about.html等） | 15分 | #2 |
| 4 | Webhook エンドポイント実装（`/api/polar/webhook`） | 30分 | OAT |
| 5 | 署名検証ロジック（HMAC-SHA256） | 20分 | #4 |
| 6 | E2E テスト（Polar test mode → Webhook到達確認） | 30分 | #1-5 |
| 7 | 本番切替 + smoke test | 15分 | #6 |

**合計見積: 約2時間**（OAT受領から出荷まで）

## 2. SDK / ライブラリ選定

- **Polar公式SDK**: `@polar-sh/sdk` （Node.js）
- Cloudflare Workers/Pages 互換性: ✅ 確認済み（fetch API ベース）
- Webhook 署名検証: 公式ドキュメント `standard-webhooks` 仕様準拠

## 3. 環境変数（Cloudflare Pages）

```
POLAR_OAT=polar_oat_xxxxx              # 受領後設定
POLAR_WEBHOOK_SECRET=whsec_xxxxx        # Product作成時に発行
POLAR_PRODUCT_ID=prod_xxxxx             # #2 で取得
POLAR_ENV=production                    # or sandbox
```

## 4. ファイル変更予定箇所

- `functions/api/polar/webhook.ts` — **新規作成**（Webhookハンドラ）
- `functions/api/polar/checkout.ts` — **新規作成**（Checkout URL返却）
- `public/about.html` — CTA href 更新
- `wrangler.toml` — env vars 参照確認

## 5. リスク・ブロッカー

| リスク | 対応 |
|--------|------|
| OAT発行遅延 | ミオさん経由で受領確認最優先（明日朝） |
| Polar側のJPY対応 | 事前確認済み（手順書3.1） |
| Webhook到達不可（Cloudflare側） | テスト環境で事前検証 |

## 6. 完了定義（DoD）

- [ ] Polar test mode で Checkout完了 → Webhook到達 → 署名検証PASS
- [ ] 本番環境で smoke test（1件購入 → メール到達）
- [ ] アオイ監査チェック通過（T-029利用規約整合）
- [ ] CTA href 更新後の about.html が公開済み

---
**次アクション**: OAT受領通知（ミオ経由）→ 即着手 → 5/19 中出荷
