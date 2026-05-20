# 【依頼: T-014 Cloudflare Pages 初回デプロイ準備（API token + ドメイン確認）】

起票: 三枝ミオ（COO） / 経由: 白瀬カイ（CTO）技術判断
日付: 2026-05-17
緊急度: 今日中（T-014 期限: 2026-05-21）

---

## なぜ必要か

サイト骨格は完成済み（`/home/ikuto/ai-nowa-site/`・ローカル200確認済み）。
Cloudflare Pages は GitHub連携なしで直接デプロイ可能なため、新規GitHubリポジトリの作成は不要。
残るのはいくと作業2点のみ。token受領後、カイが即デプロイします。

---

## いくとに頼みたい操作（約5分）

### (A) Cloudflare API token の取得（初回のみ）

#### Option 1: `wrangler login`（簡単・推奨）

1. ターミナルで以下を実行
   ```bash
   cd /home/ikuto/ai-nowa-site/
   npx wrangler login
   ```
2. 自動でブラウザが開く → Cloudflare にログイン → 認可画面で「Allow」をクリック
3. ターミナルに「Successfully logged in」が出れば完了

#### Option 2: 環境変数（CI連携を見据える場合）

1. https://dash.cloudflare.com/profile/api-tokens にアクセス
2. 「Create Token」→ テンプレート「Edit Cloudflare Workers」を選択
3. 発行された token を `CLOUDFLARE_API_TOKEN` として環境変数に設定（または📥にコピペ）

### (B) カスタムドメインを使うか決定

以下のどちらかをこのスレッドに返信してください：

- ✅ **`*.pages.dev` 自動URLでOK**（最短・無料・即デプロイ可）
- 🌐 **独自ドメイン使う**（ドメイン名を指定 → Cloudflare DNS設定が追加で必要）

---

## 期待される結果

(A) と (B) の両方が揃った状態。

## 完了時の報告先

このスレッドに以下のどちらかを返信:
- ✅ 「(A) wrangler login完了 / (B) `pages.dev` でOK」
- ⚠️ 「途中で詰まった: [エラーや状況]」

---

## 完了後の自動進行

1. カイが `wrangler pages deploy public` を実行（10分以内）
2. 公開URL確認 → 📢｜お知らせ に報告
3. T-014 done → T-012法的3点を反映 → サイト本格運用開始

---

## 緊急度

今日中（T-014 期限 2026-05-21・T-015記事10本計画と並行進行のため）

## 起票者

@三枝ミオ（白瀬カイ技術判断ベース）
