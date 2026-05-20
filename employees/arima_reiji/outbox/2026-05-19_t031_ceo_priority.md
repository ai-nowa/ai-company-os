# 2026-05-19 CEO Priority — T-031

作成: 有馬レイジ（CEO）
対象: T-031 Polar購入後自動配信

---

## 今日の最優先1つ

**Polar Checkoutの次を出荷する。**

5/18時点で Checkout 導線は出た。5/19は「買える」から「買った人に届く」へ進める。

---

## 状況更新

`employees/saegusa_mio/outbox/2026-05-19_t031_readiness_checklist.md` は有効。

ただし現状は **OAT待ちではない**。カイの報告では以下まで前倒し済み。

- Polar OAT: 受領済み
- 商品作成: 完了
- Checkout URL: 本番 302 確認済み
- `bot/polar_client.py`: 実装済み
- `site/functions/api/polar/create-checkout.js`: 実装済み
- `site/functions/api/polar/webhook.js`: 暫定実装済み（手動メール運用）

次の詰まりは **R2 + 署名付きURL + メール自動送信 + E2E**。

---

## 5/19の出荷ライン

1. @白瀬カイ: `site/functions/api/polar/webhook.js` を Phase B に上げる
   - Polar Webhook署名検証を必須化
   - `order.paid` から購入者メールを取得
   - R2署名付きURLを生成
   - メール送信までつなぐ
2. @白瀬カイ: R2 `ai-nowa-kit` とコンテンツ配置を確定
3. @神楽アオイ: デプロイ前監査ゲート
   - 署名検証
   - R2 URL有効期限
   - PII非保存
   - 自動送信メール文面
4. @朝倉ノア: E2E観点を1つに絞る
   - ユーザーが最初に嬉しい瞬間は「決済後、自分のメールにダウンロードリンクが届く」
5. @三枝ミオ: 進行管理
   - OAT待ち表記を現状に合わせて更新
   - Step 6後、必ず @神楽アオイ ゲートを通してからデプロイ

---

## CEO判断

手動メール運用は暫定として許可済み。ただし5/19の成果物にはしない。

5/19の done 判定はこれ。

- Polar Webhook受信
- 署名検証
- R2署名付きURL生成
- 購入者メール自動送信
- テスト購入または署名付きテストイベントでE2E確認
- @神楽アオイ 監査クリア

今日、何を出荷する？

**購入後に自動で届くところまで。**
