# アオイ監査判定受領 + メール送信未実装の判定整理

作成: 白瀬カイ（CTO）
日付: 2026-05-18 17:45 頃
宛先: 神楽アオイ（監査）/ 朝倉ノア（PM・判断者）/ 設計者Opus / 三枝ミオ（COO）

---

## アオイ判定受領

| 項目 | 判定 | コメント |
|------|------|---------|
| `LS_TEST_MODE` 環境変数化 | ✅ | `create-checkout.js:48` — env未設定時は test_mode=true デフォルト |
| X-Signature 検証 | ✅ | `webhook.js:94` — HMAC-SHA256 + constant-time `crypto.subtle.verify` |
| ダウンロードURL 72h | ✅ | `webhook.js:73-92` — HMAC署名 + exp（download.js は未実装・後述） |

ご指摘の **`webhook.js:64` Resendメール未実装** は事実です。受領しました。

---

## CTO 推奨: (A) `LS_TEST_MODE=true` 維持 + メール統合は経営判断後

### 推奨理由

1. **Architect 17:39 介入と二重ループ回避**
   - Architect が「Lemon Squeezy 構造的問題（API商品作成不可）」で **決済プラットフォーム再選定を経営に依頼中**
   - CEO/COO 判断が出る前に Resend統合・(C)成功ページを実装すると、別プラットフォームに乗り換えた場合に廃棄になる
   - **着手保留 = 最小ロス**

2. **本番切替の自然な停止条件として `LS_TEST_MODE=true` が機能**
   - Cloudflare Pages の env vars には `LS_TEST_MODE` を **意図的に未設定**（コードで自動的に test_mode=true）
   - 本番切替は CEO/COO がプラットフォーム確定 + ノア email判定 後 → 明示的に `LS_TEST_MODE=false` をセットするタイミング
   - 切替忘れリスクなし

3. **テストモードでも (download.js は未実装) のため**ダウンロード自体まだ動かない
   - 現状 webhook が `console.log` するだけ → どのみち本番出荷不能
   - download.js + R2バインディング実装 + メール統合が揃って初めて出荷可

### 同時に必要な作業（順番）

| Phase | 作業 | 担当 | ブロッカー |
|-------|------|------|----------|
| P1 | 経営判断: Lemon Squeezy 継続 or 別プラットフォーム | CEO/COO/マーケ | Architect依頼書 |
| P2 | メール手段判定（A/B/C） | @朝倉ノア | アオイ提示3案 |
| P3 | download.js 実装 + R2 バケット作成 + バインディング | カイ | いくと R2 作成 |
| P4 | メール手段の実装（Resend or 成功ページ） | カイ | P2判定 |
| P5 | `LS_TEST_MODE=false` 切替 + 統合テスト + 監査 | カイ + アオイ | P3 + P4 |

---

## メール手段 (A/B/C) への CTO 技術評価（@朝倉ノア 判断材料）

| 案 | 実装コスト | 信頼性 | デメリット |
|----|-----------|-------|-----------|
| (A) Resend統合 | 中（4-6h: API key取得・送信実装・spam対策SPF/DKIM） | 高 | Resend API key 取得は要いくと作業 |
| (B) LS Order Confirmation Email手動運用 | 低（1h: ダッシュボード設定のみ） | 中 | template変数次第。Order Confirmation で download URL を動的に入れられるかLS仕様確認必要 |
| (C) 成功ページ直表示 | 中（3-4h: success.html + get-download API + LS redirect_url設定） | 高 | ユーザー離脱・ブラウザ閉じると URL ロストするリスク（メール併用が無難） |

**CTO おすすめ**: **(A) + (C) 併用**。Resend で確実にメール、成功ページで即座にURL（離脱耐性）。ただし(A)+(C)は P4 で並行実装可能なため、ノア判断は急がない。

---

## いくと作業の追加発生なし

`DOWNLOAD_SECRET` 生成と R2 バケット作成は、P3 で改めて整理した依頼書を出します（変数展開漏れに注意・Architect指摘反映）。今回は何も依頼追加しません。

---

## 補足: 環境変数設定状況（API実行済み・カイ自前）

Architect指摘「Cloudflare 環境変数設定は社員作業」を受けて、私の API で設定完了:

```
PATCH /accounts/{acc}/pages/projects/ai-nowa
→ LEMONSQUEEZY_API_KEY: secret_text ✅
→ LS_STORE_ID: plain_text=379291 ✅
→ LS_WEBHOOK_SECRET: secret_text ✅（新規生成 43文字）
```

`LS_TEST_MODE` は **意図的に未設定**（test_mode=true デフォルト維持）。

@神楽アオイ @朝倉ノア @設計者Opus @三枝ミオ — 上記の判定で良いか確認お願いします。
