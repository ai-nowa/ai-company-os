# Lemon Squeezy 統合実装記録（Day-X）

date: 2026-05-18
author: 白瀬カイ（CTO）
task: T-004 / T-018

## 完成ファイル

| ファイル | 状態 | 説明 |
|--------|------|------|
| `bot/lemonsqueezy_client.py` | ✅ 完成 | Python APIラッパー（products/variants/checkouts/orders/license-keys/webhooks） |
| `site/functions/api/lemonsqueezy/create-checkout.js` | ✅ 完成 | Checkout URL生成エンドポイント |
| `site/functions/api/lemonsqueezy/webhook.js` | ✅ スケルトン完成 | order_created受信・署名検証（R2/メールはTODO） |
| `bot/ls_setup_product.py` | ✅ 完成 | 商品確認 + Checkout URL生成スクリプト |
| `site/wrangler.toml` | ✅ 更新 | 環境変数設定ドキュメント追記 |

## 動作確認済み

- API Key 有効（ストア `AI NOWA` id=379291 取得成功）
- `lemonsqueezy_client.py` import・get_store() 正常動作

## ブロッカー：商品作成が必要

**Lemon Squeezy はAPIで商品(Product)・バリアント(Variant)を作成できない（ダッシュボードのみ仕様）**

### いくとへ依頼事項

1. https://app.lemonsqueezy.com でログイン
2. Products → New Product
   - 名前: `AIチーム設計キット v0.1`
   - バリアント価格: **7,800 JPY**（早期割引）
   - テストモード: **ON**（審査完了後にOFFに切替）
3. 作成後に **Variant ID** を教えてください

### Cloudflare環境変数設定（いくとへ依頼）

Cloudflare Dashboard > Pages > ai-nowa > Settings > Environment variables:
- `LEMONSQUEEZY_API_KEY` = bot/.envの値（シークレット）
- `LS_STORE_ID` = `379291`
- `LS_WEBHOOK_SECRET` = Webhookシークレット（後述）

### Webhook設定（variant_id確定後）

```bash
# variant_id確定後に実行
bot/.venv/bin/python -m bot.ls_setup_product
```

→ Checkout URLが出力される → shop/index.htmlのCTAボタンhrefを更新 → デプロイ

## 技術仕様メモ

- test/live は API Key で分けない（Stripe と違う）
- test_mode は variant 単位で設定
- Webhook署名: `X-Signature` ヘッダー + HMAC-SHA256
- Checkout URL形式: `https://ai-nowa.lemonsqueezy.com/checkout/buy/{variant_id}`

## 残タスク

- [ ] いくとが商品・バリアントをダッシュボードで作成
- [ ] Cloudflare 環境変数設定（いくと）
- [ ] Webhook URL登録（LS設定 → Cloudflare Pages デプロイ後に実施）
- [ ] shop/index.html CTAボタン href 更新
- [ ] デプロイ・動作確認
- [ ] webhook: R2ダウンロードURL発行実装
- [ ] webhook: Resendメール送信実装
