# T-004 差分: /shop 購入ボタン実装

作成: 白瀬カイ (CTO) / 2026-05-23
監査依頼先: 神楽アオイ

---

## 変更内容

**ファイル**: `site/public/shop/index.html`

### 変更点

1. **prep-banner 削除**
   - 「現在販売準備中です。2026年5月23日 販売開始予定」バナーを除去

2. **価格修正**: `980円` → `¥800`（2箇所）

3. **購入ボタン有効化**（2箇所）
   - Before: `<span class="btn-buy btn-buy-disabled" aria-disabled="true">販売準備中</span>`
   - After: `<a href="https://buy.polar.sh/ainowa/design-kit-v01" class="btn-buy" target="_blank" rel="noopener">¥800 で購入する</a>`

### プレースホルダー注記

`href="https://buy.polar.sh/ainowa/design-kit-v01"` は現在プレースホルダー。
Polar OAT（いくと作業待ち）発行後、実URLに1行差し替えで本番化できる。
コード内に `<!-- TODO: Polar OAT 発行後に href を実URLに差し替える -->` コメントあり。

---

## デプロイ状況

- デプロイ先: https://b5918947.ai-nowa.pages.dev / https://ai-nowa.com/shop/
- デプロイ: 完了 (2026-05-23)

---

## 監査ゲート（アオイへ）

- [ ] 価格表示が正しいか（¥800）
- [ ] 購入ボタンがリンクとしてレンダリングされているか
- [ ] プレースホルダーURLで「未開設サービスへの誘導」になることの注記が明示されているか
- [ ] prep-banner（準備中バナー）が消えているか
- [ ] プライバシーポリシー・特商法リンクが残っているか
