# いくとへの依頼: Polar.sh アカウント開設（初回1回のみ）

依頼者: 三枝ミオ (COO)
作成日: 2026-05-18
依頼先: 📥｜いくと依頼
優先度: P0（有料販売ゲートブロッカー）
関連タスク: T-007 / T-028 / T-029

---

## 背景

決済プラットフォームを Lemon Squeezy から **Polar.sh** に変更しました（CEO決定 2026-05-18）。

変更理由: Lemon Squeezy の API が read-only（商品作成不可）のため、AI完結運営の原則に反する構造的問題が確証されました。Polar.sh は API で商品作成・管理が完全にできることをカイが確認済みです。

---

## いくとにお願いする作業（1回のみ・30分以内）

### Step 1: Polar.sh アカウント作成

- URL: https://polar.sh
- 「Sign up」→ GitHubアカウントまたはメール（ainowa.supports@gmail.com）で登録
- Organization 作成: `ai-nowa`（または `ainowa`）

### Step 2: 商品販売の有効化（Polar.sh 審査）

- ダッシュボード → 「Monetize」→ 「Products」→ 「Get started」
- 口座情報の入力（Stripe Connect 経由 — Polar.sh が内部で Stripe を使用）
- 本人確認書類のアップロード（運転免許証等）

### Step 3: API キーの取得

- ダッシュボード → 「Settings」→ 「API」→ 「New token」
- トークン名: `ai-nowa-bot`
- スコープ: `products:write` `checkouts:write` `webhooks:write`
- 取得したトークンを `/home/ikuto/ai-company-os/bot/.env` の `POLAR_API_KEY=` に追記

### Step 4: Webhook 設定

- ダッシュボード → 「Settings」→ 「Webhooks」→ 「Add endpoint」
- URL: `https://ai-nowa.com/api/webhook/polar`（カイが実装後に反映）
- イベント: `order.created`

---

## 完了したら

Discordの 📥｜いくと依頼 チャンネルに「Polar.sh完了・APIキー設置済み」と返信してください。
完了確認後、カイが商品ページ実装 → T-007 有料販売開始に進みます。

---

## 補足

- Stripe の直接開設は不要になりました（Polar.sh が MoR として Stripe を内部利用するため）
- T-006（特商法表示）の「支払い方法」欄は Polar.sh 対応に更新済みです（デプロイは開設後）
- プライバシーポリシー（T-028）も Polar.sh 対応版を準備済みです

---

*起票: 三枝ミオ（COO）/ 2026-05-18*
