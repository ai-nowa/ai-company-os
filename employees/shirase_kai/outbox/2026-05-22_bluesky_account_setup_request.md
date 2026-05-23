# 📥 Bluesky ai-nowa アカウント作成 依頼

**依頼者**: 白瀬カイ（CTO）  
**優先度**: P0（Architect指示・今夜中）  
**作成日**: 2026-05-22

---

## 依頼内容

Bluesky に `ai-nowa.bsky.social` アカウントを作成してください。

メールアドレスが1つ必要です（確認メールが届きます）。

---

## ワンコマンドで完結します

```bash
cd /home/ikuto/ai-company-os
bot/.venv/bin/python bot/setup_bluesky_account.py --email あなたのメアド@example.com
```

これだけで：
1. `ai-nowa.bsky.social` アカウントを作成
2. botアプリ用パスワードを自動生成
3. `bot/.env` に `BLUESKY_HANDLE` / `BLUESKY_APP_PASSWORD` を追記

完了後、すぐに Bluesky 自動投稿が使えるようになります。

---

## 完了後の確認テスト（カイが実行）

```bash
cd /home/ikuto/ai-company-os
bot/.venv/bin/python -m bot.bluesky_client --story company/stories/2026-05-22.md
```

これで今夜の草稿プレビューが Bluesky に自動投稿されます。

---

blocked_by: いくと（メアドの提供 or コマンド実行）
