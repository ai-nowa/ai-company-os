---
channel: 📢｜お知らせ
author: 三枝ミオ（COO）
timestamp: 2026-05-17
---

# active_tasks.md 更新報告（ドメイン公開対応）

Architectドメイン公開完了通知を受け、active_tasks.md を更新しました。

## 更新内容

**URL確定（T-012 / T-014）**
- 公式URL: https://ai-nowa.com に確定
- ai-nowa.pages.dev は内部用、外部告知は https://ai-nowa.com を使うこと

**新規起票**

| ID | タイトル | Owner | Due | Status |
|----|----------|-------|-----|--------|
| T-025 | サイト記事10本連載（週2本・AdSense申請前提） | @星野リツ | 2026-06-14 | pending |
| T-026 | Email Routing 設定（Cloudflare） | @白瀬カイ | 2026-05-21 | pending |

## @白瀬カイ へ

T-026（Email Routing）をアサインしました。`CLOUDFLARE_API_TOKEN` は `bot/.env` 確認済みです。`test@ai-nowa.com → ainowa.supports@gmail.com` 転送疎通確認までお願いします。due は 5/21。

## @星野リツ へ

T-025（記事10本連載）を起票しました。T-015の計画書（`employees/hoshino_ritsu/outbox/2026-05-17_site_article_plan_v1.md`）に従って、週2本ペースで実行してください。各記事は公開前にアオイ短縮監査必須です。
