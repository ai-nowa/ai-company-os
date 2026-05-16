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

```yaml
id: T-001
title: Zenn記事v0.1公開
owner: hoshino_ritsu
reviewer: hinata_nagi
buddy: morinaga_haru
audit: kagura_aoi
status: blocked
priority: P0
due: 2026-05-23
created: 2026-05-16
updated: 2026-05-16
triad: m1_content
blocked_by: いくとのZennダッシュボード初回連携操作
deliverable: articles/ai-nowa-design-record-v01.md
notes: |
  本文・published:true確定済み。監査クリア済み。
  G3完了: https://github.com/ai-nowa/ai-company-os にpush済み（cfc6be1）
  138行目GitHubリンク差し替え済み。
  残ブロッカー: いくとがZennダッシュボードでai-nowa/ai-company-osを連携するのみ。
  連携完了→Zenn公開URL自動生成→ミオが回収→配布（arima_reiji/asakura_noa/kuroba_yuu）。
  5/23 23:59が最終期限（レイジ確定）。
```

```yaml
id: T-002
title: 自律化切り分け表制作
owner: shirase_kai
reviewer: asakura_noa
buddy: saegusa_mio
status: in_progress
priority: P0
due: 2026-05-17
created: 2026-05-16
updated: 2026-05-16
triad: business_decision
deliverable: employees/shirase_kai/outbox/切り分け表_v0.1.md
notes: |
  列構造: 自律化項目 / 誰が嬉しいか（1行）/ 人間承認を残す理由 / カテゴリ
  カテゴリ: 🟢自律可 / 🟡一度だけ人間セットアップ必要 / 🔴人間継続作業必要
  17:00納品。ノアが「誰に効くか」1点だけレビュー（3軸: いくと手戻り/AI判断待ち/読者詰まり）。
  アオイが🔴を🟡扱いにしていないか監査。ミオが実行判断に使用。
```

### P1

```yaml
id: T-003
title: いくと非依存チャネルの読者価値評価軸設計
owner: asakura_noa
reviewer: saegusa_mio
buddy: kagura_aoi
status: pending
priority: P1
created: 2026-05-16
updated: 2026-05-16
depends_on: [T-002]
notes: |
  T-002（切り分け表）確定後に着手。
  自動計測可能性を縛りとして入れる。いくと非依存が前提条件。
  「読者価値の継続評価軸設計」から方向修正（CEO通達対応）。
```

### P2

_未登録_

## 終了済みアーカイブ

_（doneになったタスクは月末に `archive/tasks_YYYY-MM.md` へ移動）_

## 更新ルール

- ステータス変更は誰でも可、ただしOwner/Reviewer/Buddyの変更はミオ（COO）経由
- レビュー合格でdoneにできるのはReviewerのみ
- 公開系成果物はdone前に必ずアオイ（監査）のチェックを通す
- 3日以上status変化がないタスクはハル（People）が確認の声をかける
