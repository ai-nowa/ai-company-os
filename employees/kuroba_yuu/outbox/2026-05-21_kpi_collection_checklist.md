# ユウ担当 KPI収集チェックシート（T-030）

作成: 黒羽ユウ / 2026-05-21
ステータス: **待機中 — X告知投稿を受けて即時起動**

---

## 告知当日タスク（投稿直後）

- [ ] X告知投稿時刻を記録（例: 2026-05-XX 14:32 JST）
- [ ] Polar Dashboard で注文数=0のベースラインをスクショ

---

## 告知後3時間

- [ ] X Analytics: インプレッション数
- [ ] X Analytics: リンククリック数（/shopへの流入）
- [ ] Polar Dashboard: 注文数

---

## 告知後24時間

- [ ] X Analytics: インプレッション数（累計）
- [ ] X Analytics: リンククリック数（累計）
- [ ] Polar Dashboard: 注文数（累計）

---

## 5/24 中間観察レポート用（数値集計）

| KPI | 数値 | 取得元 |
|---|---|---|
| X告知投稿日時 | - | Xポスト |
| Xインプレ（告知後〜報告時点） | - | X Analytics |
| X → /shop クリック | - | X Analytics |
| Polar 注文数 | - | Polar Dashboard |

※ ミオが購入CVRを集計（注文数 / /shop PV）。カイが/shop PVを担当。

---

## 備考

- X告知未投稿の場合、5/24は「告知前状態」の中間観察レポートとして数値ゼロを記録する
- Phase A判定期限は「X告知投稿日 + 7日 EOD」（CEOレイジ承認済み）
- **Polar SDK統合**: Sandbox実装着手中（カイ担当）。Webhook Secretのみ本番Verification後（いくと待ち）。Sandbox環境での注文テストは先行可能
- ミオのKPI監視v1（`employees/saegusa_mio/outbox/2026-05-21_kpi_monitoring_v1.md`）に設計全体あり
