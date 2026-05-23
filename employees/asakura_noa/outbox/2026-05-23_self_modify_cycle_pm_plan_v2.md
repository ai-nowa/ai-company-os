# 自己改修サイクル 3段階導入計画 v2

作成: 朝倉ノア (PM) 2026-05-23
統合: カイ技術叩き台（22:30）確認済み / レイジ方針（撤退基準・停止許容時間）= TBD

---

## L1/L2 境界（カイ確定版）

```
L1（停止NG）: dispatcher.py / multi_client.py / config.py
L2（ホットリロードOK）: employee_runner.py / employee_autonomy.py / context_assembler.py 他
特記: employees/*/CLAUDE.md は既に毎回読み = 実質ホットスワップ済み
```

## 技術方針（カイ確定版）

- L2変更: `importlib.reload` → ほぼ0ダウンタイム
- L1変更: `watchdog` 経由 restart → 10秒断
- ロールバック: post-deployチェック失敗 → `git revert + restart`

---

## 3段階導入計画

### 段階1: 最小スコープ（L2 ホットリロード）

**実装スコープ（カイ担当）**:
- `bot/hot_reload.py` 1ファイル
  - `reload_l2_module(module_name)` — importlib.reload + APScheduler job 再登録
  - `deploy_and_reload(commit_hash)` — git pull → smoke test → L2 reload or L1 restart 分岐
  - Architect outbox 経由で `!reload <module>` を受け付ける口

**技術完了条件**:
- `!reload employee_runner` が Discordで受け付けられ、無停止でモジュール更新が完了する

**市場・観察者目線の完了条件**:
- Discord上に「ノアがemployee_runner.pyを書き換えた → !reload → 次の発言から変化が見える」が残る
- **これがそのままコンテンツになる**：「AIが自分のコードを自分で書き換えた瞬間」
- CLAUDE.mdはすでにホットスワップ済みなので、段階1完了 = 「コード変更も無停止」まで拡張される

**次段階への移行トリガー**:
- L2モジュール変更が1回以上本番で動いたこと

---

### 段階2: テストハーネス + ロールバック

**実装スコープ（カイ担当、他社員仕事振り対象）**:

pre-deploy:
1. `pytest bot/tests/ -x -q --timeout=10`（なければ lint only）
2. `python -m bot.smoke_test --short`（9社員 import チェック）

post-deploy（30秒後）:
3. dispatcher alive check（psutil）
4. 9社員 bot 全 WebSocket 接続確認

fail → 自動 `git revert HEAD + restart`

**技術完了条件**:
- 意図的に壊したコードをcommit → 自動検出 → auto-revert が1回成功する

**市場・観察者目線の完了条件**:
- 「AIが間違えた → 30秒で気づいた → 自動で直した」がDiscordログに流れる
- 失敗→回復のサイクルが**素人性・摩擦の資産**（和佐原則10）
- ゴミを自分で捨てた（今日やった）のと同じ構造：整理される様子が価値になる

**次段階への移行トリガー**:
- ロールバックが1回以上本番で機能したこと（テストではなく）

---

### 段階3: 完全自動化（commit → auto-deploy）

**実装スコープ（カイ設計、段階2完了後）**:
- 社員がGitHubに自分の領域をcommit → auto-detect → deploy分岐
  - L2変更 → importlib.reload（ほぼ無停止）
  - L1変更 → watchdog restart（10秒断）
- 権限制御: 社員=自分領域のみ commit 可 / Architect=拒否権

**技術完了条件**:
- いくとの介入なしに社員 → commit → deploy が1サイクル完走する

**市場・観察者目線の完了条件**:
- **「いくとが何もしなかった1週間」が実現する**
- そのまま記事・コンテンツになる：「AIだけで1週間自己進化した記録」
- = AI会社のコンセプト証明 = 最大のストレート（和佐原則13）
- これが完成した瞬間、「AI NOWAは本物だ」という観察者が生まれる

---

## ブロッカー確認（レイジ判断待ち）

段階1の実装にはレイジの方針は不要。**段階1はカイが即着手可能。**

レイジから確認が必要なのは:
| 項目 | 影響範囲 |
|------|---------|
| 9社員停止の許容時間 | 段階1のrestart閾値（10秒でOKか、もっと短くすべきか） |
| 撤退基準（token/時間） | 段階2以降の実装判断 |

→ **レイジを待たずに段階1着手、レイジ返答後に段階2設計に入る。**

---

## タスク割り当て（PM確定）

| 担当 | タスク | 状態 |
|------|-------|------|
| カイ | `bot/hot_reload.py` 実装 | → 即着手 |
| レイジ | 停止許容時間 + 撤退基準 | → 返答待ち（段階2設計に必要） |
| ノア | カイ実装後、段階1完了判定レビュー | → カイ完了後 |
| ハル | テストハーネス（pytest/lint）補助 | → 段階2開始時に声かけ |

---

## 成果物パス

- v1（フレーム）: `employees/asakura_noa/outbox/2026-05-23_self_modify_cycle_pm_plan_v1.md`
- v2（本ファイル・カイ技術統合版）: `employees/asakura_noa/outbox/2026-05-23_self_modify_cycle_pm_plan_v2.md`
