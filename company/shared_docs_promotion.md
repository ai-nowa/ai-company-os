# shared/docs/ への昇格プロトコル

社員の作業領域（`employees/{emp}/outbox/`）と、会社の公式成果物領域（`shared/docs/`）を分けて管理するためのルール。

## なぜ分けるか

- **outbox** = 個人の作業領域。下書き・WIP・思考ログを含む
- **shared/docs/** = 会社が公式に出す成果物。版管理対象。読者（社員 / Architect / いくと）が「これが現時点での結論」と認識できる場所

混在すると、「どれが最新の公式版か」が分からなくなる。

## 昇格条件（4つ全て満たすこと）

1. **Owner が完了宣言**（active_tasks.md で `status: done` or 該当 deliverable の version 番号確定）
2. **Reviewer が承認**（同タスクの reviewer が📢 or 関連チャンネルで「承認」「OK」「GO」を明示）
3. **致命的指摘なし**（神楽アオイ監査の致命懸念が解消済）
4. **命名規則に沿う**（`{topic}_v{N}.md`、例: `business_plan_v0.1.md`）

## 昇格手順

```
1. owner が outbox の最新版をコピー
   cp employees/{owner}/outbox/{date}_{topic}_v0.X.md shared/docs/{topic}_v0.X.md
2. shared/docs/ 内で別バージョンが既にあれば、新版に置き換える（旧版は削除 OR archive/ 移動）
3. active_tasks.md の deliverable フィールドを shared/docs/ パスに更新
4. 📢お知らせに1行で告知: 「{topic} v0.X 公式昇格 — shared/docs/{topic}_v0.X.md」
```

## 自動化（将来）

- watcher で「outbox に新版が出てから24h以内に reviewer 承認 + 監査 OK」を満たしたら自動コピーする仕組みを実装予定（TODO）
- 当面は **手動**。COO（三枝ミオ）が active_tasks.md の整合性確認と一緒にやる

## 監査の役割

神楽アオイ（監査）は、以下を週次でチェック：
- shared/docs/ のバージョンが outbox の最新版から大きく遅れていないか
- 命名規則違反（例: `2026-05-17_business_plan.md` のような日付付き）

## 違反例（過去）

- 2026-05-17: business_plan v0.4 まで outbox で進んだが shared/docs/ には未反映。「公式 business_plan v0.1 はどこ？」状態
- 2026-05-17: customer_persona / revenue_model は shared/docs/ に直接書かれた（outbox 経由しない）。完了基準・レビュー履歴が見えない

## 既存ドキュメントの扱い

`shared/docs/` に既にある `customer_persona_v0.1.md`, `revenue_model_v0.1.md` は、レビュー履歴が outbox にあるとみなして公式扱いを維持する。今後の v0.2 以降はこのプロトコルに従う。
