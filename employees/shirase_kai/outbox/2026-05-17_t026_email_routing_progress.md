# T-026 Email Routing 設定進捗

date: 2026-05-17
status: blocked_on_human（宛先アドレス確認待ち）
owner: 白瀬カイ

## 完了済み

- Email Routing 有効化: `ai-nowa.com` → `status: ready`
- Zone ID: `0a8e0446d9b34b557d1d150136de8dad`

## ブロッカー: いくとの操作が必要

### 手順（1回だけ）

1. https://dash.cloudflare.com にログイン
2. `ai-nowa.com` → `Email` → `Email Routing`
3. `Destination addresses` タブ → `Add destination address`
4. `ainowa.supports@gmail.com` を入力して追加
5. `ainowa.supports@gmail.com`（Gmail）に届く確認メールのリンクをクリック

### 完了後

いくとから「確認した」と連絡をもらえれば、残りのルール設定をAPI経由で即時完了させる：

```
- test@ai-nowa.com → ainowa.supports@gmail.com（literalルール）
- catch-all → ainowa.supports@gmail.com（全メール転送）
```

## APIトークン状況

現在のトークン（`CLOUDFLARE_API_TOKEN`）は以下に対応:
- Zone Email Routing: 有効化/ルール操作 → OK
- Account Email Routing Addresses: 登録 → **パーミッション不足**

Destination Address確認はCloudflareがGmailへ確認メールを送るフロー（ブラウザ不要だが、Gmailアクセスが必要）。
