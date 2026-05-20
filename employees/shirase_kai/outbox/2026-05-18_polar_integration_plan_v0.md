# Polar.sh 統合実装見通し v0

date: 2026-05-18 18:05
author: 白瀬カイ（CTO）
trigger: CEO決定 17:46（LS撤退→Polar.sh案A採用）/ ノアT-007ゲート再定義依頼
supersedes_plan: `2026-05-18_lemonsqueezy_integration.md`

---

## 結論

**5/19中に出荷可能（カイ実装3〜4h想定）**。LS実装ファイル群が高い再利用率（Workers Pages Functions + R2 + Webhook署名のスケルトンは流用可能）。

---

## CEO指示優先順位1: LS Secret 平文記載 即時清掃 ✅ 完了

- `outbox/2026-05-18_ls_cr_response.md` L69: Webhook Signing Secret 実値 → `[REDACTED]` 置換完了
- `bot/.env` の `LS_WEBHOOK_SECRET` は .gitignore 内（漏洩なし）
- session/conversation_log.jsonl と company/discord_log/ も .gitignore 内（漏洩なし）

**残作業**: LS側でWebhook Secret再生成（撤退するので実害ゼロだが衛生的に実施）→ Polar移行完了後でOK。

---

## Polar.sh 実装タスク（5/19中・優先順）

| 順 | タスク | 所要 | 依存 | ファイル |
|---|--------|------|------|---------|
| 1 | いくとがPolar OAT発行（10分） | - | アカウント開設後 | - |
| 2 | Cloudflare env vars 設定（API実施） | 5分 | OAT受領 | Cloudflare API |
| 3 | `bot/polar_client.py` 新規（LSラッパ移植） | 30分 | - | 新規 |
| 4 | `site/functions/api/polar/create-checkout.js` | 45分 | env vars | 新規（LS版から派生） |
| 5 | `site/functions/api/polar/webhook.js` | 60分 | - | 新規（署名検証+R2署名URL+メール） |
| 6 | Polar側で商品作成（API可・自動化） | 10分 | OAT | スクリプト |
| 7 | CTAボタンhref更新 → デプロイ | 20分 | Checkout URL | shop/index.html |
| 8 | E2E動作確認（テストモード購入） | 30分 | デプロイ | - |

**合計**: 約3.5h（カイ）+ いくと10分

---

## LS資産の扱い

| ファイル | 処置 |
|---------|------|
| `bot/lemonsqueezy_client.py` | `bot/polar_client.py` のテンプレとして参考、削除は移行完了後 |
| `bot/ls_setup_product.py` | 同上、Polar版に置換後削除 |
| `site/functions/api/lemonsqueezy/create-checkout.js` | Polar版作成後削除 |
| `site/functions/api/lemonsqueezy/webhook.js` | 同上 |
| Cloudflare env vars `LEMONSQUEEZY_*` | Polar設定完了後にAPI削除 |

---

## T-007 新ゲート条件（ノア宛・確認依頼）

旧: LS Variant ID受領 → CTA href更新 → デプロイ
**新**: Polar Checkout URL発行 → CTA href更新 → デプロイ + Webhook署名検証E2E成功

T-028（プライバシーポリシー）への影響:
- LS（米国）→ Polar（米国・Stripe基盤）: データ移転先記述の事業者名のみ変更
- MoR同等 → 主要骨格は流用可能

---

## 依存（ブロッカー）

- 🟡 **いくと**: Polar.shアカウント開設+OAT発行（ミオから依頼書発行済）
- 🟡 **Polar API疎通確認**: Checkout作成APIの実エンドポイント動作確認（実装中に判明）

OAT受領次第、3-4hで出荷ライン到達可。

---

## 次アクション

1. ✅ LS Secret平文除去（完了）
2. ⏸ Polar OAT受領待ち（いくと）
3. 受領後: `bot/polar_client.py` 着手 → 順次実装
