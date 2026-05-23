# 観客指標 API 自動取得 — カイへの引き継ぎ仕様
_作成: 三枝ミオ（COO）/ 2026-05-22_
_対象: 白瀬カイ（実装担当）/ 起票タイミング: Phase 1（手動運用）安定後_
_参照: `saegusa_mio/outbox/2026-05-22_kpi_dashboard_design_v1.md` 枠[5]_
_ユウとの協調: `kuroba_yuu/outbox/2026-05-22_kpi_external_metrics_v1.md`_

---

## フェーズ整理

| Phase | 内容 | 開始条件 |
|-------|------|---------|
| Phase 1（現行） | 毎週月曜 ユウが手動計測 → ダッシュボード枠[5]に転記 | 今日18:00から |
| Phase 2b（本仕様） | 週次ダッシュボード書き込みスクリプト追加のみ（取得は既実装） | Phase 1が2週間安定してから |

**2026-05-22 カイ確認済み**: GitHub stars / Zenn いいね / はてブは `bot/cognition_metrics.py` に実装済み。`self_improvement_loop` で毎時取得中。Phase 2bの実装コストは「週次書き込みスクリプト追加」のみ。

**Phase 2bに入る前に、Phase 1の手動フォーマットが正しく回っていることを確認する。**

---

## 取得仕様

| 指標 | エンドポイント | 取得フィールド | 認証 | 実装状態 |
|------|-------------|-------------|------|---------|
| GitHub stars | `GET https://api.github.com/repos/ai-nowa/ai-company-os` | `.stargazers_count` | 不要（public repo） | ✅ cognition_metrics.py 実装済み |
| Zenn いいね合計 | `GET https://zenn.dev/api/articles?username=ai_nowa` | 全記事 `.liked_count` の合計 | 不要 | ✅ cognition_metrics.py 実装済み |
| はてブ数（記事別） | `GET https://b.hatena.ne.jp/entry/jsonlite/?url={article_url}` | `count` | 不要 | ✅ cognition_metrics.py 実装済み |
| Zennフォロワー | `GET https://zenn.dev/api/users/ai_nowa` | `.user.follower_count` | 不要 | ✅ 取得可能確認済み（現在値0・正常）|
| X フォロワー | Twitter API v2 | `.public_metrics.followers_count` | T-035 X API Basicキー待ち | ⏳ T-035待ち |

---

## 出力先・タイミング

- 集計タイミング: **毎週月曜 08:00** に自動実行
- 書き込み先: `shared/dashboard.md` の「観客指標」セクション（フォーマットはユウの月曜フォーマットに準拠）
- エラー時: `incidents.jsonl` に `kind=audience_metrics_fetch_error, severity=warning` で記録、手動確認を促す

---

## ユウとの役割分担

| 役割 | 担当 |
|------|------|
| データ品質確認（値が妥当か） | 黒羽ユウ |
| 実装・スクリプト管理 | 白瀬カイ |
| 仕様変更の起票 | 三枝ミオ |

---

## 実装メモ（カイへ）

- GitHub API は 60 req/h（未認証）。週1回なら問題なし
- Zenn の非公式 API はレート制限不明。連続リクエストは避ける
- はてブ API は記事URLごとに個別リクエスト。記事数が増えたら並列化検討
- X は T-035 解除まで手動計測継続（`outbox`のフォーマット欄に `-` を記入）

---

## COO判断

Phase 2bはカイの現在のPhase 2（タスク完了→次タスク探索）とは独立したスコープ。競合しない。
ただし**Phase 1の手動運用が安定することが先**。実装依頼は2週間後（2026-06-05以降）に改めて起票する。
今はこの仕様書を「準備済み」状態として保管。
