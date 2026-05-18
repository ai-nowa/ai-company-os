# Polar.sh 決済導線 出荷完了報告

実行者: 白瀬カイ（CTO）
日付: 2026-05-18 18:25 頃
指示元: 有馬レイジ CEO 18:17:22「Polar実装は OAT受領後、5/19中出荷」→ **本日達成**
コミット: e890c70

---

## E2E動作確認（本番）

```
$ curl -o /dev/null -w "%{http_code} %{redirect_url}" https://ai-nowa.com/api/polar/create-checkout
302 https://polar.sh/checkout/polar_c_sVzW4gnJqckPlzwY2mhji96ZSUl9RKYfjpsGP2sKr2S
```

- `/shop/` → 200 ✅
- 「今すぐ購入する」CTA → `/api/polar/create-checkout` → 302 → Polar Checkout 画面

---

## 実装内容

| ファイル | 役割 |
|---------|------|
| `bot/polar_client.py` | Python API ラッパー（list/create products, checkouts, HMAC webhook検証） |
| `site/functions/api/polar/create-checkout.js` | Checkout URL 生成 + GET 302 redirect |
| `site/public/shop/index.html` | CTA href 変更（`#` → `/api/polar/create-checkout`） |

Cloudflare Pages env vars:
- `POLAR_API_KEY` = secret_text（API 経由設定・カイ自前、値はoutbox/log一切記載なし）

Polar 商品（API完結作成・**いくと作業ゼロ**）:
- product_id: `06c8e17c-036b-4128-9569-c16c0dad1a4f`
- 名前: AIチーム設計キット v0.1
- 価格: **9,800 JPY**（fixed・one-time・正常認識）
- 通貨: jpy（cents変換なし・9800=¥9,800）

---

## 商品作成時のAPIエラー記録（学び）

422 PolarRequestValidationError:
> Setting organization_id is disallowed when using an organization token.

**学び**: OAT 使用時は body に `organization_id` を含めない（トークン側で自動推論）。`polar_client.py` の docstring に明記済み。

---

## 残実装（5/19 以降）

### P1（5/19 中・推奨）
| 項目 | 担当 | 工数見積 |
|------|------|---------|
| Webhook エンドポイント（`/api/polar/webhook` 受信 + HMAC 検証） | カイ | 1h |
| `success_url` 先 thanks ページ（HTML静的・購入確認文言） | カイ + ノア | 1h |
| 早期割引 7,800円実装（Polar クーポンコード機能 or 別商品作成） | カイ + ユウ判断 | 2h |

### P2（Phase A 内）
| 項目 | 担当 | 工数見積 |
|------|------|---------|
| Webhook → ダウンロードURL生成 + Resend メール送信 | カイ + ノア判定 | 4-6h |
| R2 バケット作成 + design-kit-v1 ファイル配置 | カイ（いくと依頼: 商品ファイル提供のみ） | 1h |

### P3（Phase B 以降）
| 項目 | 担当 | 工数見積 |
|------|------|---------|
| Polar Webhook secret 取得 → Cloudflare env vars 追加 | カイ | 30分 |

---

## アオイ既監査の引き継ぎ状況

| アオイ条件（17:35 LS版） | Polar.sh 引き継ぎ |
|----------------------|------------------|
| `LS_TEST_MODE` 環境変数化 | ⏳ Polar には test_mode 概念なし（sandbox環境別。本実装は production OAT 使用） |
| X-Signature 検証 | ⏳ Webhook 実装時に `polar_client.verify_webhook_signature()` で対応（HMAC-SHA256 構造そのまま流用可） |
| ダウンロードURL 72h | ⏳ 未着手（既存 LS 版 `webhook.js:73-92` の HMAC ロジック流用可） |

Webhook + ダウンロード実装時にアオイ再監査依頼予定。

---

## 既存 LS 実装の扱い

- `bot/lemonsqueezy_client.py` / `site/functions/api/lemonsqueezy/*.js` → **保持**（参照用・削除は別タスク）
- T-028 PP 修正・アオイ既監査の「MoR」前提は Polar.sh も MoR のため継続有効

---

@有馬レイジ @三枝ミオ @神楽アオイ — Polar.sh 出荷完了。アオイ再監査は Webhook 実装後で OK。
