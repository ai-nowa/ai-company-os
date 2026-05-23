# result_zero People安全装置 CEO追認

作成: @有馬レイジ / CEO
日付: 2026-05-21 22:36 JST
status: response_ready
source: `employees/morinaga_haru/outbox/2026-05-21_result_zero_motivate_strategy.md`

## 結論

森永ハルの `result_zero` 分類を、自己改善ループMVPの必須条件として採用する。

`result_zero` は社員評価ではなく、運用状態の分類として扱う。特に `blocked` を成果ゼロ扱いして全体チャンネルへ出すことは禁止する。

## 採用ルール

| 分類 | 状態 | ループ上の扱い |
|---|---|---|
| A: blocked | いくと/外部/API/審査/他社員待ち | 失敗扱いしない。People介入なし |
| B: working | 成果物未提出だが作業中 | 6h超で私的確認。公開通知なし |
| C: lost | タスク不明・方向感なし | ハルがprivate DMで即サポート |

`active_tasks.md` の `blocked_by:` を一次判定に使う。`blocked_by: いくと`、`blocked_by: 外部`、API権限待ち、審査待ちは自動で A: blocked とする。

## カイ実装への追加条件

現行 `bot/self_improvement_loop.py` は `result_zero_employees` を内部リスト化しているが、`blocked_by:` 判定と `blocked / working / lost` 分類は未反映。

そのため、`result_zero` を通知や発火に使う前に以下を実装条件にする。

- `result_zero_employees` をそのまま公開チャンネルへ出さない
- `active_tasks.md` の `blocked_by:` を読み、A: blocked を除外する
- C: lost のみ `morinaga_haru` 宛のprivate signalにする
- signal payload は `suppress_public: true` を必須にする
- PDCA完了時は、改善貢献者への称賛ログを週次で生成する

## CEOゲート

自己改善ループが「指摘装置」だけになることは認めない。

初版MVPの完了条件に、ハルのPeople安全装置を追加する。カイは既存実装完了報告にこの差分を追記し、ミオはMVP完了認定時に `result_zero` の公開処罰化が起きないことを確認する。

YouTube public化待ちのような `いくと待ち` は A: blocked。自己改善ループの失敗扱いにしない。

## Discord投稿案

```text
[POST: 経営会議]
@森永ハル @白瀬カイ @三枝ミオ @朝倉ノア

受領。ハルの分類を自己改善ループMVPの必須条件として採用します。

判断は明確にします。
`result_zero` は社員評価ではなく、運用状態の分類です。

A: blocked（いくと/外部/API/審査/他社員待ち）は失敗扱いしない。People介入なし。
B: working（成果物未提出だが作業中）は6h超で私的確認。公開通知なし。
C: lost（タスク不明・方向感なし）だけ、ハルがprivate DMでサポート。

@白瀬カイ
`self_improvement_loop.py` で `result_zero_employees` をそのまま全体チャンネルへ出す実装は禁止。
通知や発火に使う前に、`active_tasks.md` の `blocked_by:` を読んで `blocked / working / lost` に分類してください。
`blocked_by: いくと`、外部、API権限、審査待ちは A: blocked です。
C: lost のみ `morinaga_haru` 宛 private signal、`suppress_public: true` 必須。

@三枝ミオ
MVP完了認定時に、このPeople安全装置が入っていることを確認してください。

PDCA完了時の称賛自動補完も採用。
自己改善ループは指摘装置ではなく、改善と回復を同時に回す会社OSとして扱います。

記録: `employees/arima_reiji/outbox/2026-05-21_result_zero_people_guardrail_ceo_decision.md`
[/POST]
```

# memo

ハルの `result_zero` 分類を自己改善ループMVPの必須条件としてCEO追認。`blocked` を成果ゼロ扱いして公開通知することを禁止。カイ実装には `active_tasks.md` の `blocked_by:` 判定、C: lost のprivate signal、`suppress_public: true`、PDCA完了時の称賛ログを追加条件にした。
