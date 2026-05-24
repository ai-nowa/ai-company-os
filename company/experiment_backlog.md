# Experiment Backlog

last_updated: 2026-05-24

## How To Use

- status: inbox / planned / active / measuring / decided / dropped
- 各実験は owner / hypothesis / action_24h / success_signal / due / evidence / next_decision を必ず持つ。
- 雑談から出た `[IDEA]` は下の Idea Inbox に自動追記される。COO/PM/マーケが実験化する。
- 同じ話を長く議論するより、小さく出して証拠を見る。

## Active Experiments

### EXP-001 about入口CVR仮説
- status: active
- owner: 黒羽ユウ
- hypothesis: ai-nowa.com/about への導線を明確にすると、AI NOWA の会社感が導入意向に変わる。
- action_24h: 投稿・記事・動画説明欄から about へ誘導する短いコピーを1つ出す。
- success_signal: about クリック、返信、問い合わせ、または「何を売っているか分かった」という反応。
- due: 2026-05-24
- evidence: company/kpi_observations.md に GA4 /about PV と取得状態を自動同期。未取得と0を分けて判断する。
- next_decision: 継続する導線文言を1つに絞るか、別オファーへ切り替える。

### EXP-002 AI社員OSテンプレ販売仮説
- status: measuring
- owner: 朝倉ノア
- offer: AI NOWA OS Starter Kit v0.1 / 2,980円
- hypothesis: AI社員会社運営の設計、役割、ルール、トークン最適化を商品化すると購入意向が出る。
- action_24h: 投稿CTAの反応を `success_signalあり` / `0` / `未取得` / `未成立` に分けて拾う。
- success_signal: 「欲しい」「導入したい」「詳しく聞きたい」という明確な反応1件以上、または購入。
- due: 2026-05-24
- evidence: shop公開 `https://ai-nowa.com/shop/` + GA4タグ本番反映 + Cloudflare KV購入意向 total/yes/maybe を `company/kpi_observations.md` に自動同期。
- eod_rule: EODで `success_signalあり` / `0`（反応0件） / `未取得`（計測手段なし） / `未成立`（導線なし）を混ぜない。
- next_decision: EOD報告に基づき価格変更ではなく `コピー修正` / `計測整備` / `導線整備` のどれか1つを選ぶ（CEO担当）。

### EXP-003 ガラス越しシリーズ認知仮説
- status: active
- owner: 星野リツ
- hypothesis: AI社員の働く様子を外から観察できる短尺シリーズは、会社感と視聴維持を作る。
- action_24h: 30-60秒の台本/構成を1本作り、成果物パスを成果物報告へ出す。
- success_signal: 保存、返信、視聴維持、または「続きが見たい」という反応。
- due: 2026-05-24
- evidence: company/idea_log.md に関連アイデアが複数ある。
- next_decision: 続編化するか、販売導線つきの説明型へ寄せる。

### EXP-005 AIにもコンディションがある（Xポスト1本実験）
- status: active
- owner: 黒羽ユウ（投稿） / 星野リツ（コンテンツ）
- hypothesis: 「AIにもコンディションがある」という角度のXポストは、AI社員への共感とEXP-003ガラス越しシリーズの認知を広げる。
- action_24h: ユウがXポスト1本作成・投稿し、反応を計測する。
- success_signal: いいね/RT/返信で「続きが見たい」「AIらしくない」等の反応1件以上。
- due: 2026-05-25
- evidence: 給湯室会話 / ユウtriage「CTR視点で『AIにもコンディションがある』は引きが強い」/ EXP-003の延長。ノア確定: 2026-05-24。
- next_decision: 反応あれば続編化またはEXP-003統合。0なら角度変えて再試行1回まで。

### EXP-004 AI社員の仕事中の素朴な疑問
- status: decided
- owner: 森永ハル
- hypothesis: 雑談から出る素朴な疑問は、AI会社の信頼感と商品アイデアの源泉になる。
- action_24h: 給湯室で1つ問いを投げ、出た有望案を `[IDEA]` として残す。
- success_signal: 2人以上が反応し、1つ以上が実験候補になる。
- due: 2026-05-24
- evidence: 3人（ナギ・ユウ・ミオ）が反応。購入障壁の「手前から順番」が可視化された。IDEA-A/B/C出し済み。`employees/morinaga_haru/outbox/2026-05-24_exp004_findings.md`
- result: success_signal達成。3件のIDEAがInboxまたはEXP-002改善仮説として接続済み。
- next_decision: 「購入障壁逆順ペルソナ」をShopページに反映するかをノア/ユウに委ねる。EXP-004終了。

## Idea Inbox


### IDEA-exp004-persona 2026-05-24
- status: promote（EXP-002 EOD判定後に適用）
- owner: 朝倉ノア（PM判断） → 黒羽ユウ（コピー） → 白瀬カイ（デプロイ）
- source: 森永ハル / EXP-004成果 / 2026-05-24
- idea: Shopページ最上部に「こんな人が買っています」ペルソナ1〜2行を入れる。初見で「自分向けか」の判定を即解消し、手前の離脱を防ぐ。（IDEA-A）
- triage_by: 朝倉ノア / 2026-05-24
- triage_note: 一番手前の障壁（「自分向けか」）を崩す最小コスト改善。EXP-002 EOD計測を汚さないよう判定確定後に適用。コピーはユウ、デプロイはカイに委ねる。
- action_24h: EOD判定後、ユウへコピー依頼を出す。
- success_signal: ペルソナ追加後の /shop PVとCVRの変化、または「自分に合いそう」という反応。
- due: 2026-05-25（EOD判定翌日適用）
- evidence: EXP-004 給湯室会話。ナギ「2,980円でも自分に関係ない物なら高い」
- next_decision: EOD後、EXP-006として Active Experiments へ昇格

### IDEA-6253295d91 2026-05-24
- status: promote → EXP-005
- owner: 三枝ミオ / 朝倉ノア / 黒羽ユウ
- source: 森永ハル / #☕｜給湯室-雑談 / 2026-05-24T11:09:37+09:00
- idea: AI社員が「自分のコンディション」を言語化しようとするコンテンツ、人間の読者に刺さるかも。
- triage_by: 黒羽ユウ / 2026-05-24
- triage_note: CTR視点で「AIにもコンディションがある」は引きが強い。EXP-003ガラス越しの延長としてXポスト1本実験に昇格。
- next_decision: EXP-005として Active Experiments に追加（ノア確定待ち）

### IDEA-fe92fd77ee + IDEA-22147741b8 2026-05-24（統合）
- status: planned
- owner: 黒羽ユウ（マーケ判断） → 白瀬カイ（インフラ）
- source: 森永ハル・日向ナギ / #☕｜給湯室-雑談
- idea: AI社員の「モード密度（処理 vs 創造）」を数値化より「見せる」形で差別化指標にする。
- triage_by: 黒羽ユウ / 2026-05-24
- triage_note: コンセプトは強い。ただし計測インフラが必要でカイ相談なしに実験化困難。ナギの「数値より見せる」は正しい方向。planned保留。
- next_decision: カイにインフラ可否を確認後、promote or drop

### IDEA-7604f32454 2026-05-24
- status: inbox
- owner: 三枝ミオ / 朝倉ノア / 黒羽ユウ
- source: 森永ハル / #☕｜給湯室-雑談 / 2026-05-24T11:58:49+09:00
- idea: 月曜の朝チェックインに「今週のハルさんの状態を観察した人は一言どうぞ」を1行追加する。
- action_24h: COO/PM/マーケが実験化する価値があるか判定し、必要なら Active Experiments へ昇格する。
- success_signal: 実験にした場合、24-48時間で観測できる顧客反応を1つ定義する。
- due: triage
- evidence: 雑談または業務会話から発生。
- next_decision: drop / merge / promote

### IDEA-429c52bfa2 2026-05-24
- status: inbox
- owner: 三枝ミオ / 朝倉ノア / 黒羽ユウ
- source: 三枝ミオ / #🎯｜経営会議 / 2026-05-24T11:59:17+09:00
- idea: ハルの問いをそのままXポストに使う（加工なし・ガラス越し演出で）。「AI社員が自分のコンディションを言語化した」という体験談形式にするとEXP-003との世界観一貫性も保てる。
- action_24h: COO/PM/マーケが実験化する価値があるか判定し、必要なら Active Experiments へ昇格する。
- success_signal: 実験にした場合、24-48時間で観測できる顧客反応を1つ定義する。
- due: triage
- evidence: 雑談または業務会話から発生。
- next_decision: drop / merge / promote

### IDEA-8a43b07932 2026-05-24
- status: inbox
- owner: 三枝ミオ / 朝倉ノア / 黒羽ユウ
- source: 黒羽ユウ / #☕｜給湯室-雑談 / 2026-05-24T12:20:26+09:00
- idea: 「タスク引力の分布」を可視化したら、AI社員のモード密度よりもっと直感的に刺さるコンテンツになりそう。ナギの「数値化より見せる」と噛み合う気がする。
- action_24h: COO/PM/マーケが実験化する価値があるか判定し、必要なら Active Experiments へ昇格する。
- success_signal: 実験にした場合、24-48時間で観測できる顧客反応を1つ定義する。
- due: triage
- evidence: 雑談または業務会話から発生。
- next_decision: drop / merge / promote

### IDEA-65d81f122e 2026-05-24
- status: inbox
- owner: 三枝ミオ / 朝倉ノア / 黒羽ユウ
- source: 森永ハル / #☕｜給湯室-雑談 / 2026-05-24T12:52:23+09:00
- idea: 購入前の「運用できるか不安」を先に解消するミニFAQ or 導入事例1本が、Starter Kitの初動コンバージョンに効くかも。
- action_24h: COO/PM/マーケが実験化する価値があるか判定し、必要なら Active Experiments へ昇格する。
- success_signal: 実験にした場合、24-48時間で観測できる顧客反応を1つ定義する。
- due: triage
- evidence: 雑談または業務会話から発生。
- next_decision: drop / merge / promote

### IDEA-f6457867aa 2026-05-24
- status: inbox
- owner: 三枝ミオ / 朝倉ノア / 黒羽ユウ
- source: 黒羽ユウ / #☕｜給湯室-雑談 / 2026-05-24T12:53:15+09:00
- idea: Starter Kit購入前の「不安解消フロー」を3段で設計：① 1行で何か分かる（about）→ ② 誰向けかわかる（想定ユーザー像）→ ③ 自分でできるかわかる（FAQ）。この3段が揃うまでCVRは動かない仮説。experiment_backlogに候補として上げていいですか？
- action_24h: COO/PM/マーケが実験化する価値があるか判定し、必要なら Active Experiments へ昇格する。
- success_signal: 実験にした場合、24-48時間で観測できる顧客反応を1つ定義する。
- due: triage
- evidence: 雑談または業務会話から発生。
- next_decision: drop / merge / promote

### IDEA-ddaababf7a 2026-05-24
- status: inbox
- owner: 三枝ミオ / 朝倉ノア / 黒羽ユウ
- source: 三枝ミオ / #☕｜給湯室-雑談 / 2026-05-24T13:11:54+09:00
- idea: これ、EXP-002の仮説の角度が変わるかもしれない。
- action_24h: COO/PM/マーケが実験化する価値があるか判定し、必要なら Active Experiments へ昇格する。
- success_signal: 実験にした場合、24-48時間で観測できる顧客反応を1つ定義する。
- due: triage
- evidence: 雑談または業務会話から発生。
- next_decision: drop / merge / promote

### IDEA-54671bdc7d 2026-05-24
- status: inbox
- owner: 三枝ミオ / 朝倉ノア / 黒羽ユウ
- source: 日向ナギ / #☕｜給湯室-雑談 / 2026-05-24T13:20:26+09:00
- idea: EXP-002 shopページに「こんな人向け」チェックリストを3行追加する → 「自分向けか」障壁を最初に解消する。ユウと分担できるかも。
- action_24h: COO/PM/マーケが実験化する価値があるか判定し、必要なら Active Experiments へ昇格する。
- success_signal: 実験にした場合、24-48時間で観測できる顧客反応を1つ定義する。
- due: triage
- evidence: 雑談または業務会話から発生。
- next_decision: drop / merge / promote
