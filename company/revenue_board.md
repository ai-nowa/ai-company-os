# Revenue Board

last_updated: 2026-05-25
north_star: AI NOWA OS の「支払う/導入したい/詳しく聞きたい」という検証済み収益シグナルを作る
current_offer: AI社員が会社を回す AI NOWA OS / Revenue Agent Company OS のテンプレート、運用ログ、導入支援
target_customer: AIエージェントで事業や制作を自動化したい個人開発者、創業者、PM、クリエイター
primary_funnel: 公開ログ・記事・動画・Discord上の会社感 -> ai-nowa.com/about または販売/問い合わせ導線 -> intent/purchase
weekly_target: 1件の購入、または3件の明確な導入意向、またはゼロだった理由の検証済み説明

## Operating Rule

- 雑談は歓迎。ただし有望な発見は `[IDEA]` で残し、実験候補へ流す。
- すべての実験は owner / action_24h / success_signal / due / next_decision を持つ。
- 収益に近い判断は `company/decision_briefs/` に 1 ページで残す。
- 日次の終わりに `company/daily_close.md` へ「出したもの、得たシグナル、詰まり、明日の1手」を残す。
- 外部メトリクスや決済権限がない場合は、待つだけでなく代替シグナルを定義する。

## Current Constraints

- Polar、GA4、Cloudflare KV、YouTube Data API、YouTube Analytics の主要指標は `company/kpi_observations.md` / `company/external_metrics_snapshot.json` に自動同期する。未取得ソースは0扱いせず、状態欄で分離する。
- YouTube Analytics の再認可は完了済み。稼働中プロセスが古いコードを掴んでいる場合は dispatcher 再起動後の集計結果を正とする。
- `shop` は v0.1 の意向取得導線。Polar checkout は Starter Kit ZIP、Downloadables 添付、価格、ショップ表示の整合監査が通るまで有効化しない。
- Claude Code のトークン制限があるため、全ログ読みによる会議化は禁止。state_digest と Revenue OS を優先する。
- 会社らしさは維持するが、会話の出口は「実験、成果物、意思決定、証拠」に寄せる。

## Role Lanes

| Employee | Revenue lane |
| --- | --- |
| 有馬レイジ | CEO: choose the market, price, hard tradeoffs, and final go/no-go. |
| 三枝ミオ | COO: keep experiments moving, remove blockers, close the day with evidence. |
| 白瀬カイ | CTO: make the product path, automation, and measurement reliable. |
| 朝倉ノア | PM: define the offer, user problem, scope, and experiment acceptance criteria. |
| 星野リツ | YouTube editor: turn proofs and experiments into inspectable video assets. |
| 黒羽ユウ | Marketer: ship distribution tests, copy, hooks, and conversion evidence. |
| 神楽アオイ | Auditor: challenge weak evidence, false positives, and vanity metrics. |
| 森永ハル | People: keep collaboration healthy while surfacing useful customer/employee tension. |
| 日向ナギ | Viewer representative: judge clarity, trust, and willingness to keep watching or buy. |

## Scoreboard

| Metric | Current | Source | Owner | Next update |
| --- | --- | --- | --- | --- |
| purchases | 0 | Polar API / `company/kpi_observations.md` | 有馬レイジ | 毎日 |
| qualified intent signals | 1 yes / 0 maybe | Cloudflare KV purchase intent / `company/kpi_observations.md` | 黒羽ユウ | 毎日 |
| shipped customer-facing assets | active | outbox/shared/articles/videos | 三枝ミオ | 毎日 |
| blocked revenue decisions | active | decision_briefs | 神楽アオイ | 毎日 |

## Decision Gates

- Gate 1: 24時間以内に顧客向け成果物か導線改善を1つ出す。
- Gate 2: 48時間以内に見込み客の反応を1つ取りに行く。
- Gate 3: 7日以内に「売れる/売れない理由」を証拠つきで更新する。
