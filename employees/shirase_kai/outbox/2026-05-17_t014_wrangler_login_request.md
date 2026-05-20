# いくと依頼: wrangler login（T-014解除 2点セット）

to: #📥｜いくと依頼
from: 白瀬カイ（CTO）
date: 2026-05-17

---

いくと、T-014 Cloudflareサイト構築の解除に **2点だけ** お願いします。

## ① T-012 運営者情報（@三枝ミオ ブロック解除）

以下3項目を教えてください（プライバシーポリシーに記載する内容）:
- **名義**: 個人名 or 屋号
- **所在地**: 都道府県レベルでOK（例: 東京都）
- **メールアドレス**: 問い合わせ先

## ② wrangler login（CF認証）

ターミナルで1コマンドだけ実行してください:

```bash
wrangler login
```

ブラウザが開くので Cloudflare アカウントでログイン → 完了。
これだけで社員側からデプロイできるようになります。

## 完了後の動き（いくと作業不要）

① + ② が揃い次第、カイが即日:
1. プライバシーページに実値を記入
2. `wrangler pages project create ai-nowa`（初回のみ）
3. `wrangler pages deploy site/public --project-name=ai-nowa`

**CF URL取得 → @三枝ミオ に報告 → AdSense申請フロー開始**

---

T-014 deadline: 05-21。①②揃えば今日中に完走できます。
