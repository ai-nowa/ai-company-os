# Active Tasks

全社員が参照する現在進行中のタスクリスト。Owner/Reviewer/Buddy を必ず付ける（文化ルール: Buddy制度）。

## スキーマ

```yaml
id: T-001                       # タスクID
title: 第1回YouTube台本作成        # 題名
owner: hoshino_ritsu            # 実作業者
reviewer: hinata_nagi           # 品質確認者
buddy: morinaga_haru            # 相談相手
status: in_progress             # pending / in_progress / review / done / blocked
priority: P0                    # P0(最優先) / P1 / P2
due: 2026-05-20
created: 2026-05-16
updated: 2026-05-16
triad: youtube                  # 関連トライアド（任意）
depends_on: []                  # 依存タスクID
deliverable: outbox/script_v1.md
notes: |
  初回なのでチュートリアル要素を入れる。
  ナギの「初見視点レビュー」を経由する。
```

## 現在のタスク

### P0（最優先）

_（Phase 1完了後、レイジとミオがここに最初のタスクを投入する）_

### P1

_未登録_

### P2

_未登録_

## 終了済みアーカイブ

_（doneになったタスクは月末に `archive/tasks_YYYY-MM.md` へ移動）_

## 更新ルール

- ステータス変更は誰でも可、ただしOwner/Reviewer/Buddyの変更はミオ（COO）経由
- レビュー合格でdoneにできるのはReviewerのみ
- 公開系成果物はdone前に必ずアオイ（監査）のチェックを通す
- 3日以上status変化がないタスクはハル（People）が確認の声をかける
