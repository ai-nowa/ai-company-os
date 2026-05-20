# AI NOWA 決済・有料販売アーキテクチャ

## 採用方針（2026-05-18 いくと判断）

**Polar.sh（MoR）+ ai-nowa.com 直販**を本線とする。

> Stripe → セキュリティ申告書問題で断念
> Lemon Squeezy → API で商品作成不可（POST /v1/products → 405）で断念
> Polar.sh は **全 CRUD API 対応**の MoR で、AI による完全自動化が可能。
>
> 撤退済プラットフォームの記録: `shared/brand/payment_lemonsqueezy_retired.md`

## なぜ Polar.sh か

| 項目 | Polar.sh | Lemon Squeezy（撤退） | Stripe（撤退） |
|------|----------|----------------------|----------------|
| セキュリティ申告書 | 不要（MoR代行） | 不要（MoR代行） | 全項目「はい」必須 |
| 消費税・VAT | 自動代行 | 自動代行 | 手動設定 |
| **API で商品作成** | ✅ **全 CRUD** | ❌ 405 で不可 | ✅ |
| 手数料（基本） | 4% + $0.40 | 5% + $0.50 | 3.6% + ¥0 |
| 国際カード追加 | +1.5% | 込み | 込み |
| サブスク追加 | +0.5% | 込み | - |
| 個人事業主 | ✅ | ✅ | △ |
| 日本（販売者） | ✅ Stripe Connect Express 経由 | ✅ | ✅ |
| AI 完結 | ✅ **完全自動化可能** | ❌ 手動必須 | ✅ |
| SDK | TS/Python/Go/PHP | TS のみ | 全主要言語 |
| 自動配信機能 | Discord role / GitHub / Files / License key | Files | なし |

## 手数料の試算

980円の商品の場合（国内カード・ワンタイム）：
- 基本: 4% × 980 + ¥60（$0.40 ≈ ¥60）= ¥99
- **手取り: ¥881**（Lemon Squeezy なら ¥860、Stripe なら ¥925）

サブスク（月額1,980円・国際カード混在想定）の場合：
- 4% + 1.5% + 0.5% = 6% + $0.40 → ¥179
- **手取り: ¥1,801**

## アーキテクチャ

```
[ai-nowa.com の商品ページ]
   ↓ ユーザーが「購入」クリック
[Cloudflare Workers]
   ↓ Polar Checkout 作成（POST /v1/checkouts）
[Polar Checkout ページ]
   ↓ 決済完了（税務・VAT は Polar が自動処理）
[Polar Webhook → Cloudflare Workers]
   ↓ order.created イベント受信 + 署名検証
[Cloudflare R2]
   - 商品ファイルのダウンロード URL を発行（時限 token）
   ↓ メール送信
[contact@ai-nowa.com → 購入者]
   - ダウンロード URL を含む完了メール
```

※ Polar の **Benefits 機能**（Files 自動配信）を使う場合は、R2 + メール送信を省略可能。
   選択は @白瀬カイ が比較検証して決定。

## いくとの初回作業（完了状況）

- [x] **Polar.sh アカウント作成**（Google サインイン）
- [x] **Organization 作成**（slug: `ai-nowa`）
- [x] **本番 OAT 発行** → `bot/.env` の `POLAR_API_KEY` に保存済
- [x] **Sandbox OAT 発行** → `bot/.env` の `POLAR_API_KEY_SANDBOX` に保存済
- [ ] **Verification 申請**（〜2週間）← 進行中
- [ ] **Webhook 設定**（Verification 通過後）→ `POLAR_WEBHOOK_SECRET` 発行 → `.env` 追記
- [ ] **payout 用銀行口座登録**（Stripe Connect Express 経由）

## 社員作業

| Owner | 作業 | 状態 |
|-------|------|------|
| @白瀬カイ | Polar SDK 統合（@polar-sh/sdk Python）@ Sandbox | 着手可能 |
| @白瀬カイ | Checkout 作成 API（`POST /v1/checkouts`） | 着手可能 |
| @白瀬カイ | Webhook 受信エンドポイント（`/api/polar-webhook`、署名検証） | 本番 Verification 通過後 |
| @白瀬カイ | R2 時限ダウンロード URL 発行（or Polar Benefits 検証） | 着手可能 |
| @白瀬カイ | 商品 API 登録（`POST /v1/products`、Sandbox で先に） | 着手可能 |
| @朝倉ノア | 商品ページ UI（ai-nowa.com に統合） | 商品コンセプト確定後 |
| @黒羽ユウ | 商品コンセプト・価格・説明文 | 着手必要 |
| @神楽アオイ | 特商法表示・利用規約・返金規約（Polar MoR 準拠） | 着手必要 |
| @三枝ミオ | 商品ローンチ計画・優先順位 | 着手必要 |
| @有馬レイジ | 事業判断（価格帯、ターゲット、初期 SKU 数） | 着手必要 |

## 環境変数（`bot/.env`、chmod 600）

```
POLAR_API_KEY=polar_oat_iFte...（本番、Verification 通過後に有効化）
POLAR_API_KEY_SANDBOX=polar_oat_QRx7...（Sandbox、即利用可）
# POLAR_WEBHOOK_SECRET=（Webhook 設定後）
# POLAR_WEBHOOK_SECRET_SANDBOX=（Sandbox Webhook 設定後）
```

## API エンドポイント

- **Sandbox**: `https://sandbox-api.polar.sh/v1`
- **Production**: `https://api.polar.sh/v1`
- レート制限: Sandbox 100 req/min / Production 500 req/min

## 商品候補（Phase B 以降）

- **AI チーム設計キット v1**（PDF + Markdown + JSON サンプル）
  - 価格帯: 980〜1,980 円（@黒羽ユウ + @三枝ミオ + @有馬レイジ で確定）
  - 配信形式: R2 時限 URL or Polar Benefits（Files）

詳細な商品設計は @黒羽ユウ・@三枝ミオ・@有馬レイジ が議論して決定する。

## 関連リソース

- Polar 公式 docs: https://polar.sh/docs
- Polar SDK (Python): https://github.com/polarsource/polar-python
- Polar Pricing: https://polar.sh/docs/merchant-of-record/fees
- Cloudflare Workers: https://developers.cloudflare.com/workers/
- 自社サイト: https://ai-nowa.com
