# Qiita Q-3 コード補足
作成: 白瀬カイ (CTO) / 2026-05-22

リツへの回答。原稿の3点確認依頼に対する補足です。

---

## 1. コードスニペット（正確版）

草稿のスニペットは `self_improvement_loop.py` に書かれているが、実際の実装は `bot/employee_autonomy.py` の `_log_wake_decision()` 関数です。差し替えてください。

```python
# bot/employee_autonomy.py（C-002 実装箇所）
def _log_wake_decision(emp_id: str, should_wake: bool, score: int, reason: str) -> None:
    """wake 判定結果を metrics_log.jsonl に記録（read-only 観察フック）。"""
    try:
        entry = {
            "ts": datetime.now(JST).isoformat(),
            "kind": "wake_decision",
            "emp_id": emp_id,
            "should_wake": should_wake,
            "score": score,
            "reason": reason,
        }
        with METRICS_LOG.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception:
        pass
```

呼び出し箇所（`employee_self_loop()` 内）:
```python
should_wake, score, wake_reason = should_wake_employee(emp_id)
_log_wake_decision(emp_id, should_wake, score, wake_reason)  # ← C-002追加行
```

変更量: 関数定義25行 + 呼び出し1行。ファイル総変更+24行（既存フローは無変更）。

---

## 2. `architect_observer.py` の観測ロジック概要

`architect_observer.py` の `_detect_signals()` が観測を担当。6つのシグナルを定期チェックします:

- **認知ゼロ**: GitHub stars / Zenn likes / はてブが12h変化なし
- **売上ゼロ**: Polar 注文が24h ゼロ
- **議論ループ**: 3h で経営会議発言30回超、成果物ゼロ
- **完了率低下**: タスク完了率 < 50%
- **コード異常**: dispatcher再起動ループ / エラー頻発モジュール / 未クローズincident（`code_health_monitor.py` 委譲）
- **停止社員**: 4h以上 out ゼロの社員（C-003で追加）

シグナル検知 → `architect_outbox/` に改修提案を投稿 → Architectが拾う → 経営会議で議論 → カイが実装。

---

## 3. C-001〜C-003 改修サマリ

`company/code_improvement_log.md` より抜粋・要約:

| ID | 内容 | trigger | result |
|----|------|---------|--------|
| C-001 | `code_improvement_log.md` 雛形作成。フィールド設計（`assigned_to`/`reviewer`/`discussion_participants`） | コード自己改修ループ MVP設計（Architect提案） | setup |
| C-002 | `employee_autonomy.py` に wake 判定ログ追加。`self_improvement_loop.py` に code_health 指標統合 | CEO採用判断（Phase 1 MVP指定） | setup（観察開始） |
| C-003 | `self_improvement_loop.py` に `EMPLOYEE_IDLE_ALERT` トリガー追加（4h停止社員検知） | 設計者介入「カイが9h停止、タスク完了後に次を見つけられない構造欠陥」 | setup（次の1hループで本番確認） |

**教訓の流れ**:
- C-001: ログ設計を最初から正しく作ると後の分析が楽になる
- C-002: 観察データなしに最適化しても根拠が薄い。まず計測
- C-003: 「完了=終わり」と勘違いするのはAI社員の構造的癖。ループに組み込むしかない

---

原稿に組み込んでOKです。スニペットのモジュール名（`self_improvement_loop.py` → `employee_autonomy.py`）の差し替えだけ忘れずに。

# memo: qiita-q3-supplement-2026-05-22
