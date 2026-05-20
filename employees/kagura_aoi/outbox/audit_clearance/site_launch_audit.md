---
slug: site-launch-audit-2026-05-17
audited_at: 2026-05-17T22:50:00+09:00
auditor: kagura_aoi
verdict: ok
---

# サイト公開監査 — https://ai-nowa.com

## チェック結果

| 項目 | 判定 | 備考 |
|------|------|------|
| プライバシーポリシー | ✅ | /privacy/index.html に掲載 |
| 免責事項 | ✅ | 同ページに掲載 |
| 運営者情報 | ✅ | 所在地・連絡先あり |
| 公式URL表記 | ✅ | ai-nowa.pages.dev → ai-nowa.com に修正済 |
| HTTPS | ✅ | Cloudflare SSL確認済 |
| 特定商取引法 | ⚠️ | 有料記事販売前に追加必要（T-006） |

## 修正内容

- `privacy/index.html` 運営者情報のWebサイトURL: `ai-nowa.pages.dev` → `ai-nowa.com`（旧ドメイン記載バグ）

## 条件付き公開可

- **現時点での公開: 可**
- **有料記事販売前に特定商取引法の表示追加が必須**（T-006で対応予定）

## GitHubリポジトリについて

- いくとの判断（2026-05-17 16:10）: **非公開維持**
- 理由: bot/.env にトークン類が含まれる可能性、実装の競合対策
- 対応: 現状のプライベート設定を維持。公開する場合は事前に監査必須。
