# AI NOWA 決済・有料販売アーキテクチャ（Lemon Squeezy 版・撤退済）

## Status: 🚫 **撤退**（2026-05-18 いくと判断・後継: Polar.sh）

> Lemon Squeezy API の調査結果、**POST /v1/products が 405 Method Not Allowed**（実テストで確認）。
> 商品作成・バリアント作成は dashboard での手動操作必須 = **継続作業前提の事業 = いくと禁止令違反**。
>
> 後継として Polar.sh（全 CRUD API + MoR + Stripe Connect Express）に移行。
> 詳細: `shared/brand/payment.md`

## 撤退の経緯（教訓）

1. **2026-05-18 14時頃**: Stripe 本番有効化でセキュリティ申告書全項目「はい」必須が発覚 → 断念
2. **同日 15時頃**: 代替として Lemon Squeezy（MoR、Stripe 傘下）採用を Architect 主導で決定
3. **同日 16時頃**: いくとが個人認証 + 銀行登録完了、JWT API キー発行
4. **同日 17時頃**: @白瀬カイ が「Lemon Squeezy API では商品作成不可」と📥に報告
5. **同日 17時半**: Architect が「API で作れるはず、調査が古い」とカイの判定を否定する CR を投稿
6. **同日 17時45分**: 実 API テスト（`POST /v1/products`）で **405 Method Not Allowed** 確認
   - **カイの判定が正しかった**ことが裏取りされた
7. **同日 17時50分**: いくと「API で作れないなら案がダメ。作れるなら社員が作れるべき」 → 撤退決定

## Architect の反省（5回目の失敗）

- 網羅調査の規範違反（公式 docs + 実 API テスト未実施で社員を訂正）
- 社員 CR の差し戻しは Architect の主観で行わず、根拠を提示するべきだった
- 詳細: `shared/rules/architect_role.md` 失敗事例#5

## Lemon Squeezy アカウントの扱い

- **審査中アカウント**: 放置（KYC 完了は不要、ただし削除もしない）
- **JWT API キー**: `.env` から削除済（`# LEMONSQUEEZY_API_KEY=（撤退済）`）
- **Webhook Secret**: Cloudflare env vars から削除済（2026-05-18）
- **個人銀行情報**: Lemon Squeezy 側で登録済だが、未使用のまま放置（後日アカウント削除も可）

## 元の比較表（参考、当時の判断材料）

| 比較項目 | Lemon Squeezy | Stripe |
|----------|---------------|--------|
| セキュリティ申告書 | 不要（MoR代行） | 全項目「はい」必須 |
| 消費税・VAT | 自動代行 | 手動設定 |
| 手数料 | 5% + $0.50 | 3.6% + ¥0 |
| 個人事業主 | ✅ 審査緩い | △ 申告書問題 |
| API 完備 | ❌ **商品作成不可**（実測） | ✅ |

※ 当時「API 完備」と判断したが、**読み取り系のみ完備で書き込み系（products/variants 作成）は dashboard 必須**だった。

## 参考リンク

- 新アーキテクチャ: `shared/brand/payment.md`
- Architect 失敗事例: `shared/rules/architect_role.md`
- 元 API ドキュメント: https://docs.lemonsqueezy.com/api
