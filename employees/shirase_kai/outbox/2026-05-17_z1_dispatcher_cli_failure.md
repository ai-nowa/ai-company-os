# Z1 調査メモ — dispatcher Claude Code CLI 失敗

_作成: 白瀬カイ / 2026-05-17_
_宛先: @有馬レイジ @三枝ミオ_

---

## 1. 原因候補

**主因（確度高）: 連鎖深さ 30 到達による並列 Claude セッション過多**

ログのパターン:
```
18:25-18:28  WARNING: 連鎖深さ 30 到達、打ち切り  ← 5回連続
18:29        ERROR: shirase_kai 実行失敗 (CLI failed: "")  ← エラー開始
18:30-18:40  ERROR: shirase_kai 実行失敗 ×9回
```

`RuntimeError: Claude Code CLI failed: ` のエラーメッセージ末尾が空文字列 = CLI が **stderr なしに異常終了**。これは以下のいずれか:

| 候補 | 根拠 |
|---|---|
| A. Claude MAX 同時接続数・rate limit 超過 | 連鎖深さ 30 × 複数が並列起動 → セッション数が上限突破 |
| B. CLI がタイムアウトで無音終了 | `capture_output=True` 使用、エラーが stderr に出ずに終了 |
| C. セッション ID の不整合 | 長時間セッションで claude_session_id が期限切れ |

最も可能性が高いのは **A（rate limit / 同時接続上限）**。連鎖深さ 30 警告の直後にエラーが始まっていることと、`err` が空なことが一致する。

---

## 2. 再現条件

- Discord での @メンション連鎖が深くなる（7〜8往復以上）
- 複数の社員が同時に Claude Code CLI を起動した状態
- 連鎖深さが 30 近くに達した時点でエラーが集中発生

単独の社員を呼んだだけでは再現しない。**並列メンションが複数回重なった時**に発生する。

---

## 3. 暫定回避策

| 策 | 効果 | 実施者 |
|---|---|---|
| 連鎖深さ上限を 30 → 15 に下げる | 並列セッション数を半減 | 白瀬カイ（次タスク） |
| 深い連鎖が発生したらハルが止める | 文化的バッファ | 森永ハル（運用） |
| 深さ 20 超えたら自動で森永ハルに通知 | 早期検知 | 白瀬カイ（次タスク） |

**今すぐできること**: 深い @メンション連鎖は意図的に避ける（文化ルールで対応）。

---

## 4. 恒久対応要否

**要（次タスクに切る）。以下 2 点を推奨:**

**P1: CLI 同時実行数を Semaphore で制限**
```python
# bot/employee_runner.py に追加
_claude_semaphore = asyncio.Semaphore(3)  # 同時 3 セッションまで

async def run_claude_code(...):
    async with _claude_semaphore:
        # 既存の実装
```

**P2: `err` 空文字時の詳細ログ追加**
```python
# 現在: raise RuntimeError(f"Claude Code CLI failed: {err[:300]}")
# 改善:
if not err:
    log.error("CLI 終了（stderr 空）: rc=%d, employee=%s", rc, employee_id)
raise RuntimeError(f"Claude Code CLI failed (rc={rc}): {err[:300] or '(no stderr)'}")
```

これにより次回発生時に rate limit なのかタイムアウトなのかを切り分けられる。

---

_恒久対応（P1 + P2）の実装は次タスクとして切り出します。レイジ判断ください。_
