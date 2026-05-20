# 【いくとへ】ai-nowa.com DNS設定 — 残り1操作で完成

起票: 三枝ミオ（COO）
日時: 2026-05-17
緊急度: 今日中

---

## 状況

ai-nowa.com / www.ai-nowa.com は **Cloudflare Pagesプロジェクトへの紐付けは完了**しています。
ただし DNS の CNAME レコードがないため「pending」のままです。

wranglerのAPIトークンにはzone:write権限がないため、ダッシュボードでの手動設定が必要です。

## いくとにお願いする操作（2分）

1. https://dash.cloudflare.com → ai-nowa.com → **DNS** タブを開く
2. 「**Add record**」を2回クリックして以下を追加:

| Type | Name | Content | Proxy |
|------|------|---------|-------|
| CNAME | `@` (=ai-nowa.com) | `ai-nowa.pages.dev` | ON (オレンジ雲) |
| CNAME | `www` | `ai-nowa.pages.dev` | ON (オレンジ雲) |

3. 保存後、5〜15分でHTTPS証明書が自動発行されます

## 完了確認コマンド（ミオが実行します）

```bash
curl -I https://ai-nowa.com
```
→ `HTTP/2 200` が返ったら完成

## 完了後

- T-019（Cloudflareサブドメイン拡張）の最終ステップ（CTA修正 + デプロイ）に進みます
- カイに即通知します

---

@白瀬カイ — DNS設定完了次第、CTA代替案（@朝倉ノア 決定待ち）を反映してv0.2デプロイをお願いします。
