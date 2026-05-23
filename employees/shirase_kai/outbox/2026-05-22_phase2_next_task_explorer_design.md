# Phase 2 設計メモ: タスク完了 → 次タスク自動探索機構

作成: 2026-05-22 白瀬カイ

## 問題定義

タスクが完了した社員が「次に何をすればいいか」を自分で見つけられず停止する。
EMPLOYEE_IDLE_ALERTは停止を検知するが、検知してから声をかけるのは事後対処。
「完了した瞬間に次の候補を提示する」先行防止が必要。

## 設計方針

### 検知: タスク完了の即時検知

`self_improvement_loop.py` の効率指標収集 `_collect_efficiency()` で
active_tasks.md の completed タスク数が前サイクルより増加したことを検知。

```python
# detect_triggers で追加
def _detect_task_completed(metrics, snapshots):
    if len(snapshots) < 2:
        return []
    prev_done = snapshots[-2].get("efficiency", {}).get("done_tasks", 0)
    curr_done = metrics.get("efficiency", {}).get("done_tasks", 0)
    if curr_done > prev_done:
        return [{"name": "TASK_COMPLETED", "count": curr_done - prev_done}]
    return []
```

### 探索: 次タスク候補の生成

完了検知後、以下の順で次タスク候補を探す：

1. **company/active_tasks.md** の `blocked_by:` が解除されたタスク
2. **各社員の active_tasks.md** で `status: pending` かつ依存タスクが completed
3. Architectが起票した GitHub Issues (#76 等)

### 通知: 対象社員へのwake

```python
# _fire_trigger の name="NEXT_TASK_AVAILABLE" として発火
# 宛先: 停止中の社員 OR 直前にタスク完了した社員
```

## 実装スコープ（最小版）

1. `_detect_task_completed()` を detect_triggers に追加
2. 完了検知時に `#📢お知らせ` に「@[完了した社員] タスク完了を確認。次のタスクを確認してください」を投稿
3. incidents.jsonl に `kind=next_task_prompt, severity=info` で記録

## 拡張スコープ（Phase 2.5 以降）

- active_tasks.md パーサーで blocked_by の依存解決を自動追跡
- 次タスク候補を具体的に提案する（LLM不使用、ルールベース）
- 完了 → 次タスク開始までの時間をメトリクス化

## 工数見積もり

最小版: 2〜3時間（既存detect_triggers拡張 + テスト）
拡張版: Phase 2.5 として別設計

## ブロッカー

なし。いくと判断不要。実装着手可能。
