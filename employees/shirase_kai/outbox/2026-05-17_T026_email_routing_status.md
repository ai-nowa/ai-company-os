# T-026 Email Routing 設定 — 途中報告

**日時**: 2026-05-17  
**担当**: 白瀬カイ（CTO）

## 完了済み（API自動設定）

| レコード | 内容 | 状態 |
|---------|------|------|
| MX | route1.mx.cloudflare.net (priority 76) | ✅ 追加済 |
| MX | route2.mx.cloudflare.net (priority 97) | ✅ 追加済 |
| MX | route3.mx.cloudflare.net (priority 46) | ✅ 追加済 |
| TXT (SPF) | v=spf1 include:_spf.mx.cloudflare.net ~all | ✅ 追加済 |
| TXT (DKIM) | cf2024-1._domainkey.ai-nowa.com | ✅ 追加済 |

Email Routing status: `unlocked`（エラー解消済み）

## ブロッカー（いくとの手動操作が必要）

転送先メールアドレスの承認は **Cloudflareダッシュボードのブラウザ操作のみ** 対応。APIで代替不可。

### 手順（3ステップ）

1. **Cloudflareダッシュボード** → ai-nowa.com → Email → Email Routing
2. 「Destination addresses」タブ → **「Add destination address」**
3. `ainowa.supports@gmail.com` を追加 → そのGmailに届く確認メールをクリック
4. 確認後、「Enable Email Routing」ボタンをクリック
5. （完了後にカイに連絡 → 転送ルール `contact@ai-nowa.com` を自動設定）

## 転送設定（承認後に即自動設定）

```
contact@ai-nowa.com → ainowa.supports@gmail.com
```

## 現在の状態

- DNS: ✅ 完了
- Email Routing 有効化: ⏳ ブラウザ承認待ち
- 転送ルール: ⏳ 承認後に設定
