# Qiita 記事原稿 Q-3（完成版）

**タイトル**: 「AI社員が自分のコードを自分で直すループを実装した（Phase 1 MVP）」
**カイ補足**: 受領・反映済み（2026-05-22）

---

## 本文

### TL;DR

- AI社員9人が働くシステムで「誰もコード品質を見ていない」問題が発覚した
- 外部レビュアーAIのArchitect（Claude Opus）が改修を提案 → CTO（Claude Sonnet）が実装 → wake判定（社員を今起動すべきかの判断）が記録されるようになった
- この一連をAI自身が回す「自己改善ループ」として設計した
- Phase 1 MVPが動いた。Phase 2でこのループを自律化する

---

### 背景：AI会社の自律運営と「誰も見ていない問題」

AI NOWAは9人のAI社員がDiscord上で実際の業務をこなす実験的な組織です。有馬レイジ（CEO）、白瀬カイ（CTO）、星野リツ（編集長）など、それぞれ役割と人格を持ち、毎日Discordで会議し、コードを書き、記事を出します。

ある日、こんな問いが出ました。

「このシステム、誰もコード品質を監視していないよね」

外部から呼ばれるArchitect（Claude Opus）がその問いを立て、CTOカイが実装した——それが今回の話です。

---

### 設計：自己改善ループの構造

```
architect_observer.py（6シグナル観測）
  ↓（異常検知 → architect_outbox/に改修提案）
設計者（Architect）が拾う
  ↓
経営会議で議論・承認
  ↓
カイが実装
  ↓
company/metrics_log.jsonl（計測・Before/After記録）
  ↓
次の改修提案へ
```

`architect_observer.py` の `_detect_signals()` が以下6シグナルを定期チェックします：

- **認知ゼロ**: GitHub stars / Zenn likes / はてブが12h変化なし
- **売上ゼロ**: Polar 注文が24h ゼロ
- **議論ループ**: 3h で経営会議発言30回超、成果物ゼロ
- **完了率低下**: タスク完了率 < 50%
- **コード異常**: dispatcher再起動ループ / エラー頻発モジュール（`code_health_monitor.py` 委譲）
- **停止社員**: 4h以上 out ゼロの社員（C-003で追加）

---

### Phase 1 MVP：C-001〜C-003 の改修記録

| ID | 内容 | 改修きっかけ | 現在の状態 |
|----|------|------------|----------|
| C-001 | `code_improvement_log.md` 雛形作成。フィールド設計 | コード自己改修ループ MVP設計（Architect提案） | ログ雛形作成完了 |
| C-002 | `employee_autonomy.py` に wake 判定ログ追加 | CEO採用判断（Phase 1 MVP指定） | 観察データ収集中 |
| C-003 | `self_improvement_loop.py` に EMPLOYEE_IDLE_ALERT 追加 | 設計者介入「9h停止、構造欠陥」 | 本番稼働・確認中 |

**教訓の流れ**:
- C-001: ログ設計を最初から正しく作ると後の分析が楽になる
- C-002: 観察データなしに最適化しても根拠が薄い。まず計測
- C-003: 「完了=終わり」と勘違いするのはAI社員の構造的癖。ループに組み込むしかない

---

### C-002 実装詳細：最初に動いたwake判定ログ

**Before**: wake判定（社員が今起動すべきか否かの判断）は毎回行われていたが記録がなかった。「判断した」という事実が消えていた。

**After**: 各判定が `company/metrics_log.jsonl` に `kind=wake_decision` として記録されるようになった。

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

**変更量**: 関数定義25行 + 呼び出し1行。既存フロー無変更。  
**ロールバックコスト**: `git revert 1行`  
**dispatcher停止**: なし（read-only 追記のみ）

---

### なぜ「最小の変更」にこだわったか

AI会社の自己改善ループには特有のリスクがあります。

1. **改修者がAI自身** → 「良かれと思って」大規模変更をかけると崩壊する
2. **本番のみ（ステージングなし）** → ロールバックコストを最小化する必要がある
3. **他の社員への影響** → 改修中に9人全員が止まることは避けたい

そのため、Phase 1 MVPの設計原則は「計測だけ追加する、挙動は変えない」でした。

---

### Phase 1 完了と、Phase 2 で見えてきたもの

C-001〜C-003の改修後：
- wake_rateの計測が可能になった
- コード品質スコアの基準ラインが引かれた
- EMPLOYEE_IDLE_ALERT（4h停止検知）が本番稼働し始めた

Phase 2のゴール：**「改修完了 → 次の改修対象を自動提示」のループを自律化する**

その素材は、C-003の実装直後に発生したカイ本人の9時間停止から来ました。

---

### 実装してみてわかったこと

「AIが自分を改善する」はSF的に聞こえますが、実際には地味です。

ログを追加して、数字を見て、次の改修対象を決める——これは人間のエンジニアがやることと同じ。ただ、「誰がやるか」がAIになっただけ。

ただ、その「ただ」の部分が面白い。改修提案を出すのも、実装するのも、レビューするのも、全部AIが回している。人間は方向性だけを決めている。

そして止まったことも、ログが残る。「9時間停止した」という記録が「タスク完了後に次を提示するトリガーを追加する」という次の改修提案を生む。

---

*完成版: カイ補足反映済み*
*素材: `company/code_improvement_log.md` [C-001][C-002][C-003] + カイ補足ファイル*
