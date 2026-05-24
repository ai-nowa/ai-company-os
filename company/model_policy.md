# Model Policy

last_updated: 2026-05-24

## Purpose

AI NOWA のモデル選択は「安いほどよい」でも「常に最強」でもなく、手戻りを最小化するための投資判断として扱う。

## Current Defaults

| Situation | Claude employee | Codex employee | Reason |
| --- | --- | --- | --- |
| micro | sonnet / low | gpt-5.5 / low | 軽い確認。速さと節約を優先。 |
| routine | sonnet / medium | gpt-5.5 / medium | 通常応答。過剰思考を避ける。 |
| high-judgment routine | sonnet / high | gpt-5.5 / high | COO/CTO/PM/マーケ/監査は手戻り影響が大きい。 |
| real conversation | sonnet / high | gpt-5.5 / high | 人間/社員同士の文脈は雑に返すと会社感が崩れる。 |
| work | sonnet / high | gpt-5.5 / high | 実装、設計、台本、レビュー。 |
| executive | opus / xhigh | gpt-5.5 / xhigh | 経営判断、公開判断、価格、撤退、契約。 |
| crisis | opus / max | gpt-5.5 / xhigh | 障害、炎上、法務、セキュリティ、P0。 |

## Invariants

- 有馬レイジは CEO として常に Codex `xhigh`。
- Claude は通常 `sonnet`、重要判断だけ `opus`。
- Claude fallback は `opus -> sonnet`, `sonnet -> haiku`。
- 具体モデル ID ではなく alias を優先し、Claude Code 側の最新安定版へ追従する。
- ルーティング結果は `company/usage_metrics.jsonl` に `route_tier`, `route_reason`, `route_escalated`, `fallback_model` として記録する。

## Tuning

再起動なしで調整したい値は `company/dynamic_config.yaml` の `model_policy` を編集する。構造変更や新しい tier 追加は `bot/model_policy.py` とテストを更新する。
