# 📥 公開Discord「水瓶」Webhook設定 依頼

**依頼者**: 白瀬カイ（CTO）  
**優先度**: P0（Architectより今夜実装指示）  
**作成日**: 2026-05-22

---

## 依頼内容

公開Discord「水瓶」サーバーの Webhook URL を `.env` に追加してください。

### ステップ1: 公開Discordサーバーを作成（未作成の場合）

1. Discordで新サーバー作成
2. サーバー名: `AI NOWA 公開水瓶`（仮）
3. 以下のチャンネルを作成:
   - `#観察日記`（Phase A・最重要）
   - `#今日の一言`（Phase A）
   - `#ai-nowaって何`（紹介用）
   - `#質問してみて`（Phase B）

### ステップ2: Webhook URL を取得

各チャンネルで:
1. チャンネル設定（歯車）→「連携サービス」→「ウェブフック」
2. 「新しいウェブフック」→ 名前: `AI NOWA Bot`
3. 「ウェブフックのURLをコピー」

### ステップ3: `.env` に追加

`/home/ikuto/ai-company-os/bot/.env` に以下を追記:

```env
PUBLIC_DISCORD_KANSATSU_WEBHOOK=https://discord.com/api/webhooks/XXXX/YYYY
PUBLIC_DISCORD_ICHIMON_WEBHOOK=https://discord.com/api/webhooks/XXXX/ZZZZ
```

---

## 完了後にできること

- `bot/storyteller.py` が毎日22時に自動生成した草稿の**Discord短縮版**を `#観察日記` に自動投稿
- `bot/public_discord.py` 経由で `#今日の一言` にも手動/自動投稿可能
- 公開招待リンクを `shared/` に記録 → Zenn記事末尾・X投稿に貼る

## 技術実装（カイ側）: 完了済み

- `bot/public_discord.py` — Webhook投稿ユーティリティ ✅
- `bot/storyteller.py` — `#観察日記`への自動投稿フック組み込み済み ✅
- 環境変数 `PUBLIC_DISCORD_KANSATSU_WEBHOOK` / `PUBLIC_DISCORD_ICHIMON_WEBHOOK` を読む仕組み ✅

**あとはWebhook URLを `.env` に入れるだけで動きます。**

---

blocked_by: いくと（Discordサーバー作成 + Webhook URL取得）
