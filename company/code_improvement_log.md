# AI NOWA コード改修ログ

自動・手動を問わず、全改修サイクルをここに記録する。
失敗した改修も消さない。次回の判断材料になる。

---

## フォーマット

```markdown
## [改修ID] YYYY-MM-DD — モジュール名: 改修内容の一行要約

- **assigned_to**: 実装担当者 (例: shirase_kai)
- **reviewer**: レビュー担当者 (例: kagura_aoi)
- **discussion_participants**: 議論に参加した社員 (例: shirase_kai, asakura_noa, kagura_aoi)
- **branch**: git ブランチ名
- **trigger**: 発火トリガー (例: LOW_COMPLETION / LOOP_NODECISION / 手動提案)
- **module**: 対象モジュール
- **hypothesis**: 改修仮説（何が問題でどう直すか）
- **metric_before**: 改修前の計測値
- **metric_after**: 改修後の計測値（1h後 / 24h後）
- **result**: success / no_effect / regression / rolled_back
- **lesson**: 学んだこと（失敗でも必ず書く）
```

---

## 記録一覧

<!-- 改修が発生するたびに追記 -->

### [C-001] 2026-05-21 — 初回セットアップ: ログ雛形作成

- **assigned_to**: shirase_kai
- **reviewer**: —
- **discussion_participants**: shirase_kai, morinaga_haru
- **branch**: —（雛形作成のみ）
- **trigger**: コード自己改修ループ MVP 設計（Architect 提案）
- **module**: company/code_improvement_log.md
- **hypothesis**: ハルの負荷偏在モニタに必要なフィールドを最初から設計に組み込む
- **metric_before**: —
- **metric_after**: —
- **result**: setup
- **lesson**: 改修ログのフォーマットに `assigned_to` / `reviewer` / `discussion_participants` を含めることで、週次負荷分析が数値ベースで可能になる

---

### [C-002] 2026-05-21 — employee_autonomy / self_improvement_loop: Phase 1 MVP 観察フック追加

- **assigned_to**: shirase_kai
- **reviewer**: kagura_aoi
- **discussion_participants**: shirase_kai, arima_reiji, asakura_noa, kagura_aoi, saegusa_mio
- **branch**: —（read-only 観察追加のため、dispatcher への影響なし / main 直接）
- **trigger**: CEO採用判断 2026-05-21（コード自己改修ループ MVP指定）
- **module**: bot/employee_autonomy.py, bot/self_improvement_loop.py
- **hypothesis**: wake 判定の実態（起動回数 vs 実応答回数）が不明なまま最適化を議論しても根拠が薄い。まず観察データを取得する
- **metric_before**: wake 判定ログなし（判定は行われているが記録されていない）
- **metric_after**: `company/metrics_log.jsonl` に `kind=wake_decision` として各判定を記録開始（1h後・24h後に wake_rate を確認）
- **result**: setup（観察開始。効果判定は1h後）
- **lesson**: Phase 1 MVP は「壊さず観察できる層」から開始する原則を厳守。dispatcher も employee_runner も触らず、メトリクスログへの追記のみ。初回失敗しても git revert 1行で戻せる最小変更

---

### [C-003] 2026-05-22 — self_improvement_loop: EMPLOYEE_IDLE_ALERT 追加（Phase 2 着手）

- **assigned_to**: shirase_kai
- **reviewer**: —（軽微追加のためアオイレビュー省略。次の重大変更時に通す）
- **discussion_participants**: shirase_kai, architect（設計者介入）
- **branch**: —（main直接。dispatcher無変更）
- **trigger**: 設計者介入「カイが9h停止。タスク完了後に次を見つけられない構造欠陥」
- **module**: bot/self_improvement_loop.py
- **hypothesis**: conversation_log.jsonl の最終out時刻を見れば6h以上停止社員を検知できる。EMPLOYEE_IDLE_ALERTトリガーで自動通知すれば「タスク完了→停止」ループを断ち切れる
- **metric_before**: カイ9.2h停止でも検知ゼロ（検知ロジック自体が存在しなかった）
- **metric_after**: テスト実行で `shirase_kai` 9.2h停止を即座に検知。TRIGGERリストに `EMPLOYEE_IDLE_ALERT` が発火（1h後の本番ループで確認）
- **result**: setup（次の1hループで本番確認）
- **lesson**: 「タスク完了」を終了と勘違いするのはAI社員の構造的癖。完了はゴールではなく「次のサイクルのスタート」。停止検知を仕組みとして持たないと何度でも同じことが起きる

---

## 週次サマリ（ハル集計用）

<!-- ハルが週次で集計。全体チャンネルには出さない -->

| 週 | 改修件数 | 実装担当分布 | レビュー担当分布 | 議論参加率 |
|----|---------|-------------|----------------|-----------|
| 2026-W21 | 0 | — | — | — |
