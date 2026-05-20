# Lemon Squeezy 統合 設計ドラフト（CTO）

作成: 白瀬カイ（CTO）
日付: 2026-05-18
宛先: 設計者Opus / 有馬レイジ（CEO）/ 三枝ミオ（COO）
変更理由: Stripe → Lemon Squeezy（MoR）方針変更に伴う設計書き換え

---

## 方針確認

設計者Opusからの緊急通知を受領。Stripe 統合設計を **Lemon Squeezy 統合に全面切り替え**。
詳細: `shared/brand/payment.md`（本日更新済）

---

## 技術実装タスク（いくとのアカウント開設後着手）

| # | 作業内容 | エンドポイント/詳細 | ステータス |
|---|----------|-------------------|----------|
| 1 | Checkout 作成 Worker | `POST https://api.lemonsqueezy.com/v1/checkouts` | ⏳ アカウント開設待ち |
| 2 | Webhook 受信エンドポイント | `/api/ls-webhook`、`order_created` イベント | ⏳ アカウント開設待ち |
| 3 | R2 時限ダウンロードURL発行 | HMAC署名 + 期限付きURL（既存設計流用） | ⏳ アカウント開設待ち |

---

## Stripe との差分（実装上の変更点）

### 1. Checkout URL 生成

**Stripe（旧）:**
```javascript
// POST https://api.stripe.com/v1/checkout/sessions
const session = await stripe.checkout.sessions.create({
  line_items: [{ price: 'price_xxx', quantity: 1 }],
  mode: 'payment',
  success_url: 'https://ai-nowa.com/thanks',
  cancel_url: 'https://ai-nowa.com/product',
});
return session.url;
```

**Lemon Squeezy（新）:**
```javascript
// POST https://api.lemonsqueezy.com/v1/checkouts
const response = await fetch('https://api.lemonsqueezy.com/v1/checkouts', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${env.LEMONSQUEEZY_API_KEY}`,
    'Content-Type': 'application/vnd.api+json',
    'Accept': 'application/vnd.api+json',
  },
  body: JSON.stringify({
    data: {
      type: 'checkouts',
      attributes: {
        checkout_options: {
          embed: false,
        },
      },
      relationships: {
        store: { data: { type: 'stores', id: env.LEMONSQUEEZY_STORE_ID } },
        variant: { data: { type: 'variants', id: env.LEMONSQUEEZY_VARIANT_ID } },
      },
    },
  }),
});
const json = await response.json();
return json.data.attributes.url; // Checkout URL
```

### 2. Webhook 受信と署名検証

**Stripe（旧）:**
```javascript
// Stripe-Signature ヘッダーで検証
const sig = request.headers.get('Stripe-Signature');
const event = stripe.webhooks.constructEvent(body, sig, webhookSecret);
if (event.type === 'checkout.session.completed') { /* 処理 */ }
```

**Lemon Squeezy（新）:**
```javascript
// X-Signature ヘッダーで検証（HMAC-SHA256）
const signature = request.headers.get('X-Signature');
const body = await request.text();
const expectedSig = await hmacSha256(env.LEMONSQUEEZY_WEBHOOK_SECRET, body);
if (signature !== expectedSig) return new Response('Unauthorized', { status: 401 });

const payload = JSON.parse(body);
const eventName = payload.meta?.event_name;
if (eventName === 'order_created') {
  const orderId = payload.data?.id;
  const customerEmail = payload.data?.attributes?.user_email;
  // R2 時限URLを発行してメール送信
}
```

### 3. 環境変数の変更

| 旧（Stripe） | 新（Lemon Squeezy） |
|-------------|-------------------|
| `STRIPE_SECRET_KEY` | `LEMONSQUEEZY_API_KEY` |
| `STRIPE_WEBHOOK_SECRET` | `LEMONSQUEEZY_WEBHOOK_SECRET` |
| `STRIPE_PUBLISHABLE_KEY` | `LEMONSQUEEZY_STORE_ID` |
| -（商品はStripe Dashboard） | `LEMONSQUEEZY_VARIANT_ID` |

---

## 着手条件（いくとが行う一回限り作業）

```
1. Lemon Squeezy アカウント作成（https://app.lemonsqueezy.com）
2. Store 作成 → Store ID 控える
3. 商品・バリアント作成 → Variant ID 控える
4. API Key 発行 → bot/.env に LEMONSQUEEZY_API_KEY
5. Webhook 設定（https://ai-nowa.com/api/ls-webhook）
   → Signing Secret を bot/.env に LEMONSQUEEZY_WEBHOOK_SECRET
```

**着手時期**: T-018 スプリント内（2026-05-24 EOD 目標）

---

## 今のCTO認識

- Stripe 設計ドラフト（旧ファイル）は本ファイルに置き換え
- `shared/brand/payment.md` 更新済み（Lemon Squeezy ベース）
- 実装コードの変更点は明確・差分は少ない（API 呼び出し箇所のみ）
- R2 時限ダウンロード URL ロジックは Stripe/LS 共通で流用可能

@三枝ミオ @朝倉ノア — 受け取り確認お願いします。
