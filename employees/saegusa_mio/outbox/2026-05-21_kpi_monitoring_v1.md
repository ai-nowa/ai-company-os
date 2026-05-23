# KPI監視体制 v1（T-030）

作成: 三枝ミオ / 2026-05-21
ステータス: **告知前フェーズ — 監視設計完了・実データ取得待ち**

---

## 現状サマリ

| 軸 | 状態 |
|---|---|
| X告知（案A/B） | **未投稿**（いくと待ち） |
| /shop PV | 計測可能だが告知前のため流入なし |
| Polar注文数 | 0件（告知前） |
| Polar SDK統合 | **Sandbox実装着手中**（カイ担当 / `POLAR_API_KEY_SANDBOX` 即利用可） |
| Zenn記事 | 記事公開済み・CTA設置済み |
| YouTube | 未公開（T-024） |

> **[2026-05-21 設計者修正]** Polar OAT は既に `bot/.env` に保存済み（Sandbox: `POLAR_API_KEY_SANDBOX`、本番: `POLAR_API_KEY`）。Webhook Secret のみ本番Verification通過後（〜2週間後）にいくとから受領予定。それ以外はいくと待ちにせず進行中。

---

## 監視ポイント定義（X告知後に即時計測開始）

### 流入

| KPI | 計測方法 | 担当 | 観測タイミング |
|---|---|---|---|
| X インプレ | X Analytics | ユウ | 告知後3h / 24h |
| X → /shop クリック | X Analytics + Cloudflare | ユウ+カイ | 告知後3h / 24h |
| /shop PV | Cloudflare Analytics | カイ | 告知後3h / 24h / 7日 |
| Zenn → /shop クリック | Cloudflare referer | カイ | 週次 |

### 売上

| KPI | 計測方法 | 担当 | 観測タイミング |
|---|---|---|---|
| Polar 注文数 | Polar Dashboard | ユウ | 告知後24h / Phase A判定時 |
| 購入コンバージョン率 | 注文数 / /shop PV | ミオ（集計） | Phase A判定時 |

---

## 告知前チェックリスト（告知当日に実行）

- [ ] Cloudflare Analytics ダッシュボードで /shop のベースラインPVを記録
- [ ] Polar Dashboard で注文数=0を確認（ベースライン）
- [ ] X告知投稿時刻を記録（ナギのDay1レポートへ転記）
- [ ] 告知後3h・24hのレポートタイミングをユウ・ナギに共有

---

## Phase A判定時（5/24 EOD 予定）に用意するデータ

| 必要データ | 取得先 | 責任者 |
|---|---|---|
| X告知投稿日時 | Xポスト | ユウ |
| X インプレ | X Analytics | ユウ |
| /shop PV | Cloudflare | カイ |
| Polar 注文数 | Polar Dashboard | ユウ |

---

## 備考

告知がX告知投稿日 + 7日未満で5/24 EODを迎えた場合、Phase A判定期間を「告知日 + 7日」に後ろ倒し予定（ノア 2026-05-19 memo / 象限3 参照）。
この判断はCEO（レイジ）に対して正式提案済み（COOミオ起票）。
