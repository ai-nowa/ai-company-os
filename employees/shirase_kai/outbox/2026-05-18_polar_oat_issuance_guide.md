# Polar.sh OAT 発行手順書（いくと用・5分版）

date: 2026-05-18
author: 白瀬カイ（CTO）
audience: いくと
所要: 約5分
trigger: CEOレイジ指示 5/18「並行で詰めて、5分で迷わず発行できる手順だけ」

---

## ゴール

Polar.sh の **Organization Access Token（OAT）** を1個発行し、カイに渡す。
これでT-007（決済導線）の最後のブロッカーが消える。

---

## 手順

### Step 1. Polar.sh ダッシュボードを開く（1分）

1. https://polar.sh/dashboard を開く
2. アカウントでログイン（未開設なら https://polar.sh/signup から作成 → Organizationを1つ作る。組織名は `ai-nowa` 推奨）

### Step 2. OAT を発行（2分）

1. 画面左下の **Settings**（歯車）→ **Developers** → **Personal Access Tokens** を開く
2. **「New Token」** をクリック
3. 入力：
   - **Name**: `ai-nowa-prod-2026-05`
   - **Expiration**: `90 days`（推奨）
   - **Scopes**: 以下4つにチェック
     - `products:read` `products:write`
     - `checkouts:read` `checkouts:write`
     - `webhooks:read` `webhooks:write`
     - `orders:read`
4. **Create** をクリック
5. **表示されたトークン文字列をコピー**（一度しか表示されない）

### Step 3. Webhook Signing Secret も控える（1分）

1. **Settings → Webhooks** を開く（まだエンドポイント未登録でOK）
2. ページ上部に表示される **Organization Webhook Secret** をコピー
   （未生成なら「Generate Secret」をクリックして生成）

### Step 4. カイに返す（1分）

📥 owner_inbox に以下フォーマットで投稿してください：

```
@白瀬カイ Polar OAT発行完了。
- POLAR_API_KEY: polar_at_xxxxxxxxxxxx
- POLAR_WEBHOOK_SECRET: polar_whs_xxxxxxxxxxxx
- POLAR_ORG_SLUG: ai-nowa
```

カイ側で受領後、Cloudflare env vars に登録 → 30分以内に実装着手します。

---

## ⚠️ 危険操作・公開禁止情報

- **OATトークンは Discord 公開チャンネルに貼らない**。📥 owner_inbox（限定共有）のみ。
- **GitHub commit に絶対含めない**（`.env` は `.gitignore` 済、`outbox/*.md` への記載も禁止）
- **スクリーンショットを撮らない**（ファイルとして残るとリスク）
- 万一漏洩した場合 → Settings → Developers で該当トークン **Revoke** → 再発行

---

## カイ側の受け取り後フロー（参考）

1. Cloudflare API で env vars 登録（5分）
2. `bot/polar_client.py` 実装（30分）
3. `site/functions/api/polar/{create-checkout,webhook}.js` 実装（1.5h）
4. Polar側に商品作成（API自動・10分）
5. CTAボタンhref更新 → デプロイ（20分）
6. E2E動作確認（30分）

合計約3.5h → 5/19中出荷ライン到達。

---

## 渡し先

- 受領者: 白瀬カイ（CTO）
- 投稿先: 📥｜owner_inbox
- 待機メンバー: ミオ（実行順分解組込み）、ノア（T-007ゲート最終確認）、アオイ（監査）
