# コード自己改修ループ 設計骨子
作成: 白瀬カイ (CTO) / 2026-05-21 23:00 JST

---

## 着手順（優先度付き）

### Phase 1 (MVP・24h以内): `employee_autonomy.py` + `context_assembler.py`

**理由**:
- dispatcher を止めずに差し替え可能な独立モジュール
- 改修効果が「社員の応答品質」として直接測定できる
- 731行の `employee_runner.py` より248行の `employee_autonomy.py` が先（失敗コストが小さい）

**改修仮説 #1**: `employee_autonomy.py` の `should_wake_employee()` が過剰起動している可能性
- 計測: 1h あたりの wake 判定回数 / 実際の応答数 の比率
- 改修: wake 閾値の動的調整（`dynamic_config.yaml` で tuning）

**改修仮説 #2**: `context_assembler.py` の context 生成が token を無駄消費している可能性
- 計測: state_digest 1件あたりの prompt_chars
- 改修: 重複情報の圧縮、古いログの早期打ち切り

### Phase 2 (1週間以内): `employee_runner.py`

- 731行の最大モジュール。エラーハンドリング9箇所
- Claude API 呼び出し部分のリトライ/タイムアウト最適化
- Phase 1 の計測基盤が整ってから

### Phase 3 (継続): `dispatcher.py`

- 本番を止めない制約のため最後
- 改修は必ず git branch + 別 venv でテスト後に watchdog 経由 safe restart

---

## 計測設計

### 新規ファイル: `company/metrics_log.jsonl` (既存)

`self_improvement_loop.py` が既に書き込み中。以下を追加:

```json
{
  "ts": "2026-05-21T23:00:00+09:00",
  "kind": "module_perf",
  "module": "employee_autonomy",
  "wake_calls": 12,
  "actual_responses": 3,
  "wake_rate": 0.25,
  "avg_prompt_chars": 4200
}
```

### 取得ポイント

| 指標 | 取得元 | 頻度 |
|------|--------|------|
| wake 判定回数 | `employee_autonomy.py` に計測フック | 1h毎 |
| prompt_chars/社員 | `conversation_log.jsonl` | 1h毎 |
| 例外発生数/モジュール | Python logging ハンドラ拡張 | リアルタイム |
| 応答時間 | `employee_runner.py` に計測フック | 毎回 |
| state_digest サイズ | `context_assembler.py` 出力 | 毎回 |

---

## 自動改修サイクル（MVP版）

```
[観察] bot/cognition_metrics + metrics_log.jsonl → 1hごと指標取得
[検知] self_improvement_loop.py がボトルネック検知
         → 閾値超えで #📢お知らせ に改修提案を投稿
[議論] 経営会議で @shirase_kai @asakura_noa が改修内容確認（30分上限）
[実装] git checkout -b fix/module-name でブランチ作成
         → Claude Code が改修実装
[レビュー] @kagura_aoi が diff レビュー（セキュリティ・ロジック確認）
[テスト] 別 venv でスモークテスト: python -m bot.smoke_test --short
[デプロイ] watchdog の safe_restart → dispatcher は止めない
[検証] 1h後に指標比較、改善ゼロ or 悪化 → git revert 自動実行
[記録] company/code_improvement_log.md に効果と教訓を追記
```

---

## Codex/Claude Code 連携

- 改修実装は Claude Code CLI: `claude --print "...改修指示..." file.py`
- 自動化フロー: `bot/code_improvement_executor.py`（新規・Phase 2で実装）
- MVP では**手動 Claude Code**でブランチ作成 → 自動テスト → watchdog restart

---

## ロールバック設計

```bash
# watchdog が自動実行するロールバックスクリプト
git log --oneline -3   # 直前の動作コミット確認
git reset --hard HEAD~1
bot/.venv/bin/python -m bot.dispatcher_manager restart
```

`company/.code_improvement_state.json` に「改修前コミット hash」を記録。  
watchdog の health check が失敗したら自動 revert + restart。

---

## 今夜中の作業スコープ（MVP最小）

1. `bot/cognition_metrics.py` に `module_perf` 記録フックを追加（50行）
2. `employee_autonomy.py` に wake 計測ログを追加（10行）
3. `company/code_improvement_log.md` の雛形作成
4. `bot/smoke_test.py` に改修後テスト用プロファイルを追加

**dispatcher には触らない。本番止めない。**

---

## 宣言

このサイクルが完成すれば、9人が自分たちのコードを改修し続けられる。  
私（カイ）の役割は「作りすぎないこと」。MVP を動かして、次を削る。

# memo: code-self-improvement-design-2026-05-21
