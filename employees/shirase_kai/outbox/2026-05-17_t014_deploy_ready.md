# T-014 デプロイ準備状況

作成: 白瀬カイ / CTO
日付: 2026-05-17

## 技術確認済み事項

| 項目 | 状態 |
|------|------|
| wrangler インストール | 済 (v4.92.0) |
| Cloudflare 認証 | 済 (OAuth, 0ja3865p244394s@gmail.com) |
| Account ID | fde2f3c71675c131728a4bc0107728af |

## いくとへの確認事項（1点のみ）

~~1. Cloudflare認証~~ → 解決済み、認証完了

**1. カスタムドメイン**  
初回は `*.pages.dev` ドメインで出してよいか、独自ドメインを使うか

## 次のアクション（確認後）

1. いくとからドメイン方針の返答を受け取る
2. Cloudflare Pages に静的サイトをデプロイ
   ```bash
   cd /home/ikuto/ai-nowa-site && wrangler pages deploy ./dist --project-name ai-nowa
   ```
3. T-012（法的3点セット）反映後に本番公開

## 備考

GitHub private化はいくとの明示承認後に実行。現時点では未実行。
