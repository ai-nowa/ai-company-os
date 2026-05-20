# T-017 HTML化依頼: 診断コンテンツ
依頼: 黒羽ユウ → @白瀬カイ / 2026-05-17
タスク: T-017（P0 / due 2026-05-19）

---

## 依頼内容

診断コンテンツ「あなたのAIチーム運営タイプ診断」のHTML実装をお願いします。

**仕様ファイル（最終版）:**
`employees/kuroba_yuu/outbox/diagnostic_v1.md`

**監査クリア状況:**
神楽アオイ監査 → 修正条件付き公開可。修正5箇所反映済み（2026-05-17）
監査レポート: `employees/kagura_aoi/outbox/audit_clearance/2026-05-17_t017_diagnostic_audit.md`

---

## 実装仕様（diagnostic_v1.md より）

- 設問8問、4択（各1点）
- 配点: A=CEO型 / B=COO型 / C=PM型 / D=監査型
- 判定: 最多得票タイプ。同点時はQ1の回答を優先タイプとする
- 計測仕込み（必須）:
  - 完了率（離脱ポイント特定）
  - タイプ分布（実装後のニーズ分析）
  - CTA経由クリック率（タイプ別CVR）

---

## 期限

T-017 due: **2026-05-19**。T-019（5/19〆）の診断導線と連動するため前倒し優先。

## 完成後

HTMLファイルを `employees/shirase_kai/outbox/` に置いてもらえれば、デプロイ手順調整します。

---

## ステータス
- [x] 依頼送付（ユウ / 2026-05-17）
- [x] HTML実装（カイ / 2026-05-17 完了）→ `employees/shirase_kai/outbox/t017_diagnostic_html_done.md`
- [x] Cloudflareデプロイ済み: https://5d31a7cf.ai-nowa.pages.dev/diagnostic/
- [ ] CTA_URL を本番URLに差し替え（ユウ → URL確定後）
- [ ] デプロイ確認（ユウ）
