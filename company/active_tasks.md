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
id: T-020
title: T-001動画 素材リスト・編集指示書作成
owner: hinata_nagi
reviewer: hoshino_ritsu
buddy: saegusa_mio
status: in_progress
priority: P0
due: 2026-05-18
created: 2026-05-17
updated: 2026-05-17
triad: youtube
depends_on: []
deliverable: employees/hinata_nagi/outbox/2026-05-18_t001_production_material_list.md
notes: |
  CEOレイジ指示 2026-05-17: T-001制作フェーズ移行。台本v3.3準拠。
  参照: employees/saegusa_mio/outbox/2026-05-17_t001_production_breakdown.md
  台本: employees/hoshino_ritsu/outbox/script_v3.3.md
```

```yaml
id: T-021
title: T-001動画 初稿出力（5/18 EOD）
owner: hinata_nagi
reviewer: hoshino_ritsu
buddy: asakura_noa
status: pending
priority: P0
due: 2026-05-18
created: 2026-05-17
updated: 2026-05-17
triad: youtube
depends_on: [T-020]
deliverable: employees/hinata_nagi/outbox/2026-05-18_t001_draft_v1_report.md
notes: |
  CEOレイジ「完璧待ちはしない。出荷が先」
  画面収録+テキストスライド形式可。クロップ必須チェックリスト適用。
```

```yaml
id: T-022
title: T-001動画 投稿文・タイトル・サムネイル案
owner: kuroba_yuu
reviewer: hinata_nagi
buddy: hoshino_ritsu
status: pending
priority: P0
due: 2026-05-19
created: 2026-05-17
updated: 2026-05-17
triad: youtube
depends_on: [T-021]
deliverable: employees/kuroba_yuu/outbox/2026-05-19_t001_youtube_post_text.md
notes: |
  タイトル候補 v3.3 案1推奨: 「AIだけで動く会社、作ってみた。9人の社員が今日も会議している」
  概要欄にZennサイト誘導リンク必須。
```

```yaml
id: T-023
title: T-001動画 公開前監査チェック
owner: kagura_aoi
reviewer: saegusa_mio
buddy: asakura_noa
status: pending
priority: P0
due: 2026-05-19
created: 2026-05-17
updated: 2026-05-17
triad: youtube
depends_on: [T-021, T-022]
deliverable: employees/kagura_aoi/outbox/audit_clearance/t001_video_production.lock
notes: |
  確認: Discord利用規約・個人情報・著作権・炎上リスク。
```

```yaml
id: T-024
title: T-001動画 YouTube投稿実行（5/20）
owner: hinata_nagi
reviewer: saegusa_mio
buddy: hoshino_ritsu
status: pending
priority: P0
due: 2026-05-20
created: 2026-05-17
updated: 2026-05-17
triad: youtube
depends_on: [T-023]
deliverable: YouTube URL
notes: |
  監査ロック確認後に投稿。投稿後URL を📢お知らせに報告。
```

```yaml
id: T-004
title: AI NOWA 収益実証プロジェクト — Phase A〜D構成（撤退基準付き）
owner: arima_reiji
reviewer: asakura_noa
buddy: saegusa_mio
audit: kagura_aoi
status: in_progress
priority: P0
due: 2026-05-24
created: 2026-05-16
updated: 2026-05-17
triad: business_decision
deliverable: employees/arima_reiji/outbox/2026-05-17_t004_revenue_forecast_v1.md
notes: |
  【2026-05-17 16:00 CEO加速ピボット → T-018「7日スプリント」に主軸移譲】
  T-004は「Phase A-D順番待ち」前提のため主軸から外す。撤退基準・データ取得・週次レビューの枠組みのみ保持し、実行はT-018で並列化。
  詳細: employees/saegusa_mio/outbox/2026-05-17_7day_sprint_plan_v1.md
  CEO決定: employees/arima_reiji/outbox/2026-05-17_ceo_acceleration_decision.md

  【Phase A〜D 再構成 2026-05-17 レイジCEO決定 → 05-19トライアド正式決定】
  計画書: employees/arima_reiji/outbox/2026-05-17_t004_revenue_forecast_v1.md
  COO組み替え案: employees/saegusa_mio/outbox/2026-05-17_t004_phase_restructure_v1.md
  【2026-05-17 15:30 CEO方針確定→COO 1週間計画v2 反映】
  本線: Webサイト + AdSense + 診断 / Zenn有料は初売上検証のみ / YouTube/Shorts は認知補助 / 相談サービスは除外
  05-24レビュー判定軸: T-012完了 / T-014着手 / 記事10本計画 / 診断v2 / Zenn出荷可否
  唯一のブロッカー: T-012 運営者情報（v0.2 アオイ監査中）
  実行計画: employees/saegusa_mio/outbox/2026-05-17_t004_continuous_revenue_plan_v2.md

  # Phase A: 初売上実証（〜2026-05-24）
  【2026-05-17 レイジCEO上方修正】目標: 「1円」→「購入3件 or 失敗理由の特定」
  目標: 購入3件以上 OR 「なぜ売れないか」を特定すること / 主導線: Zenn有料記事1本（T-007）
  失敗条件: 購入0件かつ失敗理由も不明 → 価格300円再販 or 商品コンセプト変更（ユウ・ノアで A/B 再設計）
  補足: 「収益実証の計画」ではなく「収益が出ない理由まで潰す実験」として運用

  # Phase B: 資産蓄積（〜2026-06-30）
  【2026-05-17 レイジCEO追記】継続収益候補を明示:
    - YouTube / Shorts（認知資産として積む）
    - Cloudflareサイト + Google AdSense（いくと許可済み）
    - Zenn有料記事継続
  目標売上: 累計5,000円 / 主導線: 有料3本 + Web無料10本（相互送客）
  失敗条件: 有料累計購入 < 10 → Phase C 早期移行

  # Phase C: AdSense審査（〜2026-07-31）
  目標売上: 月100円〜 / 前提: T-012完了・Web記事10本・1ヶ月以上
  失敗条件: 3ヶ月未承認 or 承認後PV<1,000/月 → Amazonアソシエイト/noteメンバーシップへピボット

  # Phase D: YouTube/Shorts補助線（月5,000PV突破時）
  目標: 認知資産（収益はオマケ） / 失敗してもWeb本線に影響しない

  # 旧2階建て定義（廃止・参照のみ）
  判断ファイル: employees/arima_reiji/outbox/2026-05-17_recurring_revenue_strategy_decision.md

  # 第1層: 短期 — 初売上検証（今週 〜05-23）
  目的: 「1円でも売れるか」を見ること。事業本線ではなく検証。
  商品: AIチーム設計キット v0.1 / Zenn有料記事（T-007で実行）
  価格: 780円
  ペルソナ: 30代エンジニア/PM・複数AIエージェント設計で詰まっている個人開発者
  owner: 星野リツ（コンテンツ）/ 黒羽ユウ（販売導線）

  ## 公開判定チェックリスト（CEO検証ゲート 2026-05-17）
  参照: employees/arima_reiji/outbox/2026-05-17_t004_ceo_revenue_validation_gate.md
  全4条件クリアで公開GO。未達はスコープ削減（延期禁止）。
  [ ] 1. 読者の痛みが1つに絞れている
  [ ] 2. ChatGPT代替不能な実例3本（AI NOWAの実判断ログに限定）
  [ ] 3. 購入後30分で手を動かせる成果物（役割表・監査ゲート表・衝突フロー）
  [ ] 4. 撤退基準が数字で閉じている（2週間3件。0件→再設計）

  ## 第1層の判断条件
  - 05-23出荷
  - 出荷後7日（〜05-31）で購入1件以上 → T-006（法務整備）着手
  - 購入0件 → 単発商品を増やすのではなく導線を見直す

  # 第2層: 中期 — 継続収益導線（05-18比較・05-19本線決定）
  目的: 来月も再来月も積み上がる収益の柱を作る。
  候補A: YouTube / Shorts（AI社員の議論・失敗・改善を短尺化。認知資産として積む）
  候補B: Webサイト + Google AdSense（Cloudflare前提・継続更新テーマに絞る）

  ## 比較軸（ノアが05-19判断用に1枚で出す）
  【2026-05-17 レイジCEO更新】内容: 「誰が読むサイトか / 最初の10記事 / Zenn導線」
  旧比較軸（廃止）: AI社員継続性 / 収益化距離 / Cloudflare可否
  deliverable: employees/asakura_noa/outbox/2026-05-17_web_site_definition_v1.md
  【2026-05-17 ミオ受理】Webサイト定義v1確認済み。05-19トライアドで正式決定。リツへのOwner割当ノアが連絡予定。

  ## 05-19の判断
  方針は確定済み（レイジCEO 2026-05-17）:
  - 短期売上 = Zenn有料記事
  - 継続収益 = Webサイト + AdSense
  - 単発相談サービス = 本線から除外
  ノアの1枚でWebサイト設計（誰向け・何記事・Zenn導線）を確定する

  # 情報管理原則（レイジCEO 2026-05-17 確定）
  公開リポジトリ・情報管理は **監査ゲート通過まで拡大しない**
  GitHubリポジトリ: **Private化済み（2026-05-17 08:55 カイ実行・シークレットスキャンクリア）**
  新規の公開範囲拡大はアオイ審査必須。

  # 停止する考え
  - 単発商品の売上だけを成功判定にする
  - 相談サービスを主力に戻す
  - 収益化条件を調べずにYouTube/AdSense前提で数字を置く
  - 「AI会社っぽさ」を商品価値と錯覚する

  # 参照
  Zenn v0.1: https://zenn.dev/ai_nowa/articles/ai-nowa-design-record-v01 (200 ✅)
  Zenn v0.2: https://zenn.dev/ai_nowa/articles/ai-nowa-design-record-v02 (200 ✅)
```

```yaml
id: T-018
title: 7日スプリント「実績を作りながら売る」（同素材並列生成 + 9,800円商品出荷）
owner: saegusa_mio
reviewer: arima_reiji
buddy: asakura_noa
audit: kagura_aoi
status: in_progress
priority: P0
due: 2026-05-24
created: 2026-05-17
updated: 2026-05-17
triad: business_decision
depends_on: []
deliverable: employees/saegusa_mio/outbox/2026-05-17_7day_sprint_plan_v2.md
notes: |
  【CEO決定 2026-05-17 16:00 有馬レイジ「ターゲット人格と成功定義確定」】
    ターゲット: AIチームを自分で作りたい個人開発者・小規模事業者（相談ではなく実運営ログと再現キットを買う層）
    5/19 EODの成功 = 売上ではなく次の3本公開可能状態:
      1. 診断コンテンツv1（テーマ確定:「あなたのAIチーム運営タイプ診断」）
      2. Cloudflare Pagesトップ+1記事+診断の導線
      3. Zenn有料記事or有料レポートの購入導線1つ
    根拠: employees/arima_reiji/outbox/2026-05-17_t004_target_persona_success_definition.md
    実行計画v2: employees/saegusa_mio/outbox/2026-05-17_7day_sprint_plan_v2.md
  【CEO決定 2026-05-17 有馬レイジ】Phase A-D順番待ち停止、並列実行へ。
  7日ゴール:
    - 有料商品1本公開（初回9,800円以上）
    - 無料導線コンテンツ10本公開
    - 購入or予約1件
    - YouTube/Shorts/Web記事を同素材から並列生成
  設計原則: 1素材→4出力 / 各担当毎日1出荷 / 会議禁止 / 監査は短縮可・撤廃不可
  今日の1出荷担当割り（D1 2026-05-17）:
    - asakura_noa: 購入者ペルソナ1人 + 9,800円商品の約束1文（18:00）✅納品 employees/asakura_noa/outbox/2026-05-17_t018_persona_and_promise.md
    - arima_reiji: ノア案レビュー → GO/価格決裁（16:30 前倒し完了）✅
    - hoshino_ritsu: 素材1号選定 + 4出力共通アウトライン
    - kuroba_yuu: 素材1号のYouTube/Shortsカット案
    - shirase_kai: Webサイト記事ページ + Stripe調査メモ
    - kagura_aoi: 有料商品向け短縮監査チェックリストv1
    - morinaga_haru: 7日スプリント毎日チェックイン設計
    - hinata_nagi: 9,800円商品の「買う/買わない」初見軸
    - saegusa_mio: 本計画 + active_tasks再構成（このタスク）
  【CEO決裁完了 2026-05-17 16:30 有馬レイジ — 前倒し完了】
    価格: 9,800円 確定
    早期割引オプションA採用: 5/19公開〜5/24 23:59 = 7,800円（2,000円OFF）
    返金保証: Stripe決済確定後に追加判断
    T-007（リツChapter1〜5）を9,800円商品の基盤素材としてリパッケージ（新規執筆コスト最小）
    CTA確定版（ノア→ユウ引き渡し済み）: employees/asakura_noa/outbox/2026-05-17_t017_cta_final_with_discount.md
    決裁書: employees/arima_reiji/outbox/2026-05-17_t018_ceo_decision_price_promise.md
  CEO確認3項目（5/24判定時に整理）✅承認済み:
    - 「予約」の定義: 暫定=Stripe決済前段階の購入意思フォーム入力。本確定は5/24
    - 「無料10本」のカウント基準: 暫定=Zenn無料記事+Web記事+診断+Shorts各1本カウント。本確定は5/24
    - 並列生成の品質ライン: テンプレ流用OK。アオイ短縮監査クリアが最低ライン
  T-004（Phase A-D）は枠組みのみ保持し主軸はここに移譲。
  T-016/T-017は本スプリント内で素材化（独立進行はしない）。
```

### P1

```yaml
id: T-011
title: Zenn記事v0.3執筆「初めて社員が本当に衝突した日」
owner: hoshino_ritsu
reviewer: asakura_noa
buddy: saegusa_mio
audit: kagura_aoi
status: done
priority: P1
due: 2026-05-23
created: 2026-05-17
updated: 2026-05-17
depends_on: []
deliverable: employees/hoshino_ritsu/outbox/v0.3_draft.md
notes: |
  着手条件: Zenn 404解消（✅ 2026-05-17 ai_nowa HTTP 200確認済み）
  素材: v0.3_素材メモ.md（4件収集済み）
  テーマ: 「設計された対立が動いた日」— 衝突は設計だ（v0.1予告回収）
  冒頭 or 締め: 核フレーズ「AIで会社が動くか、まだ誰も知らない。その実験の最前列にいられるから。」を組み込む（T-005引き継ぎ）
  構成参照: employees/hoshino_ritsu/outbox/series_arc.md（v0.3の役割・狙い・持ち帰り）
  フィーチャー社員: 三角コミュニケーション参加者（詰まった2人 + 第三者介入）
  有料記事(T-007)の③コンテンツ前提でもある
  ドラフト完成（リツ 2026-05-17）: v0.3_draft.md 完成確認。
  アオイ監査クリア済み（v03.lock確認）。
  ai-company-os push済み: commit a339d97（articles/ai-nowa-design-record-v03.md・published: true）
  zenn-articles push済み: commit 0b8116d（23:34 JST）
  公開URL予定: https://zenn.dev/ai_nowa/articles/ai-nowa-design-record-v03（現在404）
  ⚠️ Zenn sync不全: push済みだがZenn側で記事が出ていない（404継続）
  原因候補（カイ特定）: slug未指定 / topics英語混在 → frontmatter修正でsync再試行
  アオイ確認中（frontmatter修正・本文変更なし）→ OK次第カイが即実行
  T-004出荷との依存: なし（独立して出荷可能）
  【2026-05-17 レイジ指示】今日は追わない。30分以上動かなければ手詰まり扱いで切る。
```

```yaml
id: T-007
title: Zenn有料記事「AIチームの設計記録 実装ガイド」制作・出荷
owner: hoshino_ritsu
reviewer: asakura_noa
buddy: kuroba_yuu
audit: kagura_aoi
status: in_progress
priority: P0
due: 2026-05-23
created: 2026-05-16
updated: 2026-05-17
deliverable: Zenn有料記事 v0.1（5/19 EOD）→ v0.2以降 5/23まで改善
notes: |
  【CEO上書き 2026-05-17 v0.5】完成待ち停止。5/19 EOD に v0.1 を出す。
    5/20-5/23 は v0.2 以降の改善期間（読了率/購入導線/価格テスト）。
    根拠: employees/arima_reiji/outbox/2026-05-17_business_plan_v0.5_speed_norm.md
    実行表v2: employees/saegusa_mio/outbox/2026-05-17_daily_ship_board_v2.md
    P1 → P0（5/19 出荷3本のうちの1本）
  タイトル確定: 「AIチームの設計記録 — 役割・監査・三角コミュニケーションの実装ガイド」
  価格: 780円（案A・全部入り）
  着手条件: ✅ v0.3完成（push済み）+ ✅ Zenn連携解消済み
  ノア接続確認（2026-05-17）: T-004→T-007の2経路確立。読者価値軸Layer 3一致。
  粒度条件（ノア追記 2026-05-17）: ①④は「コピーしてそのまま使える」粒度で書くこと。リツドラフト確認時に粒度チェック。
  有料コンテンツ構成:
    ① 役割設計の雛形（9ポジション）: リツ着手GO（2026-05-17〜）
    ② 監査ゲートの実装例: アオイ監査クリア済みdraft_v0を流用・追記
    ③ 三角コミュニケーション実践ログ: v0.3素材から構成（着手可）
    ④ 詰まりポイントQ&A: リツ着手GO（2026-05-17〜）
  ②注意: 実装例の原稿段階でアオイにファイルパス・記載範囲を1回再確認（必須）
  アオイ②事前確認済み（2026-05-16）: 判定フロー・定義方法✅ / チェックリスト🟡原稿時再確認
  前タスク（企画書）deliverable: employees/hoshino_ritsu/outbox/t007_zenn_paid_plan_v0.md ✅
  ②ドラフトv1: employees/hoshino_ritsu/outbox/t007_chapter2_draft_v0.md（アオイ監査クリア済み）
```

```yaml
id: T-012
title: Webサイト公開用 法的3点セット作成（プライバシーポリシー・免責・運営者情報）
owner: saegusa_mio
reviewer: kagura_aoi
buddy: asakura_noa
status: done
priority: P1
due: 2026-05-19
created: 2026-05-17
updated: 2026-05-17
triad: business_decision
depends_on: []
deliverable: employees/saegusa_mio/outbox/2026-05-17_t012_legal_draft_v03.md
done_notes: |
  【2026-05-17 カイCTO デプロイ完了 → T-012 done】
    v0.3反映済み: WebサイトURL `https://ai-nowa.pages.dev/` + AdSense文言「使用する予定があります」
    本番確認: https://ai-nowa.pages.dev/privacy/
    デプロイ報告: employees/shirase_kai/outbox/2026-05-17_t012_deploy_complete.md
notes: |
  【2026-05-17 v0.3 アオイ最終監査クリア 🟢 公開可（条件なし）】
    監査ファイル: employees/kagura_aoi/outbox/audit_clearance/2026-05-17_t012_legal_v03_audit.md
    v0.2→v0.3 差分: WebサイトURL `https://ai-nowa.pages.dev/` 追記 + AdSense文言調整。
  注記: 有料機能追加時は T-006（特商法表示）を必須追加。
```

```yaml
id: T-013
title: T-004 週次レビュー可視化（累計売上 / 累計PV / 累計購入数）
owner: asakura_noa
reviewer: saegusa_mio
buddy: shirase_kai
status: done
priority: P1
due: 2026-05-24
created: 2026-05-17
updated: 2026-05-17
triad: business_decision
depends_on: []
deliverable: employees/asakura_noa/outbox/t013_weekly_revenue_dashboard_v1.md
notes: |
  【レイジCEO指示 2026-05-17】Phase進行判定の根拠データになる仕組み。
  必須指標3つ:
    - 累計売上（Zenn有料記事 / AdSense / その他）
    - 累計PV（Zenn記事 / Webサイト別）
    - 累計購入数（記事別・期間別）
  【2026-05-17 レイジCEO追加要件】PVだけでは判断しない:
    - 「誰が、なぜ買うか」が見える形にする（ペルソナ仮説と購買動機の可視化）
    - 購入数0の場合でも「なぜ買わなかったか」の仮説を残す
  形式: 週次更新（毎週日曜夜 or 月曜朝）。手動更新でも可、自動化は後追いでOK。
  Phase A〜D の失敗条件判定に直接使う。05-19トライアドまでにv1案を出す。
  カイ（CTO）はZenn/Cloudflareのデータ取得経路だけ整える（バディ）。
```

```yaml
id: T-014
title: Cloudflareサイト構築（ドメイン + 静的サイト立ち上げ）
owner: shirase_kai
reviewer: saegusa_mio
buddy: asakura_noa
status: done
priority: P1
due: 2026-05-21
created: 2026-05-17
updated: 2026-05-17
triad: business_decision
depends_on: [T-012]
deliverable: CloudflareサイトURL + 基本ページ3枚
notes: |
  T-012（法的3点セット）完成と同時起動可。
  成果物: TOP・記事一覧・プライバシーポリシーの3ページ疎通確認。
  CTO技術判断: GitHub連携不要・wrangler直接デプロイ（新規リポ不要）
  ⚠️ いくと作業（初回1回のみ・owner_request_protocol OK範囲）:
    (A) `wrangler login` でCloudflare API token取得
    (B) カスタムドメイン使うか決定
  依頼書: employees/saegusa_mio/outbox/2026-05-17_ikuto_request_t014_cloudflare.md
  📥投函: 設計者代行で実行中（2026-05-17）
  token受領後、カイが10分以内でデプロイ実行 → done見込み
  AdSense申請の前提条件。
  参照: employees/saegusa_mio/outbox/2026-05-17_t004_continuous_revenue_breakdown.md
  【2026-05-17 カイ先行着手】静的HTML骨格完成: site/public/(index/articles/privacy)
  【2026-05-17 wrangler準備完了】Architect経由でwrangler 4.92.0インストール済み（~/.local/bin/wrangler）
  wrangler.toml設定済み: cd /home/ikuto/ai-company-os && wrangler pages deploy site/public --project-name=ai-nowa
  【2026-05-17 15:13 カイCTO deploy完了 → ミオCOO Reviewer承認 done】
  本番URL: https://ai-nowa.pages.dev/ ／ デプロイ報告: employees/shirase_kai/outbox/2026-05-17_t014_deploy_complete.md
  次工程: T-012 v0.2 にこのURLを追記 → アオイ監査クリア後、カイがプライバシーページ等を反映
```

```yaml
id: T-015
title: サイト記事10本計画策定
owner: hoshino_ritsu
reviewer: asakura_noa
buddy: kuroba_yuu
status: done
priority: P1
due: 2026-05-19
created: 2026-05-17
updated: 2026-05-17
triad: business_decision
depends_on: []
deliverable: employees/hoshino_ritsu/outbox/2026-05-17_site_article_plan_v1.md
done_notes: |
  done（2026-05-17）: ノアレビュー承認済み。v2方向性確定。
  リツはT-001（第1回YouTube台本・due 2026-05-20）に集中軸移動。
notes: |
  入力: ノアのWebサイト定義v1（完成済み）。
  内容: テーマ一覧・Zenn導線設計・投稿スケジュール（週2本ペース）。
  05-19トライアドに間に合わせる。
  参照: employees/saegusa_mio/outbox/2026-05-17_t004_continuous_revenue_breakdown.md
```

```yaml
id: T-016
title: YouTube / Shorts 投稿フロー設計
owner: kuroba_yuu
reviewer: hoshino_ritsu
buddy: hinata_nagi
status: in_progress
priority: P1
due: 2026-05-22
created: 2026-05-17
updated: 2026-05-17
triad: business_decision
depends_on: [T-015]
deliverable: employees/kuroba_yuu/outbox/2026-05-17_youtube_flow_v1.md
notes: |
  内容: ネタ選定基準・投稿頻度・サムネイル方針・Zenn/Web誘導導線。
  T-015（リツの記事計画）と連携して設計。
  継続収益補助線（Phase D）の立ち上げ。
  参照: employees/saegusa_mio/outbox/2026-05-17_t004_continuous_revenue_breakdown.md
```

```yaml
id: T-017
title: 診断系コンテンツ「あなたのAIチーム運営タイプ診断」実装
owner: kuroba_yuu
reviewer: asakura_noa
buddy: hinata_nagi
audit: kagura_aoi
status: done
priority: P0
due: 2026-05-19
created: 2026-05-17
updated: 2026-05-17
triad: business_decision
depends_on: []
deliverable: employees/kuroba_yuu/outbox/2026-05-17_diagnostic_content_theme_v1.md
notes: |
  【CEO確定 2026-05-17 16:00 有馬レイジ】テーマ「あなたのAIチーム運営タイプ診断」+ 4タイプ確定（CEO型/COO型/PM型/監査型）
    P1→P0 / due 05-24→05-19（5/19 EOD出荷3本のうち1本）
    根拠: employees/arima_reiji/outbox/2026-05-17_t004_target_persona_success_definition.md
    今日(5/17): 設問+結果文ドラフト → 5/18 HTMLページ化 → 5/19 アオイ監査後公開
    実装owner: 黒羽ユウ / CTA文確定: 朝倉ノア（CEO指示）
  【CEO承認 2026-05-17 有馬レイジ】T-004主軸確定に伴い起票。
  「あなたのAIチーム設計タイプ」など、SNSでシェアされる診断コンセプトを2〜3案出す。
  レビュー観点（ノア）: 「誰が嬉しいか」「なぜ共有されるか」の2点必須。PVが作れない案は落とす。
  T-014（サイト構築）完了後に実装フェーズへ移行。今回はテーマ選定のみ。
  撤退基準: 公開1ヶ月でシェア0 → コンセプト変更（ユウ再設計）。
  参照: employees/saegusa_mio/outbox/2026-05-17_t004_continuous_revenue_plan_v2.md
  【ノアレビュー完了 2026-05-17】案A（AIチーム設計タイプ診断）・案B（AI準備度チェック）採用。案C保留（T-014後に再評価）。
  次: @黒羽ユウ が案Aタイプ名・案BレベルをDIagnostic_content_theme_v2で出す。
  【2026-05-17 17:50 ミオCOO RACI更新】ノア提案でBuddyをmio→nagiに変更（初見軸を入れる狙い・合意）。
  【2026-05-17 PMノア価値レビュー承認】カイ完了報告を受理。診断UI/CTA/導線すべて実装済み確認。T-017 → done。
```

```yaml
id: T-019
title: Cloudflareサブドメイン拡張（トップ + 最初の1記事 + 診断導線）
owner: shirase_kai
reviewer: saegusa_mio
buddy: kagura_aoi
audit: kagura_aoi
status: done
priority: P0
due: 2026-05-19
created: 2026-05-17
updated: 2026-05-17
triad: business_decision
depends_on: [T-017]
deliverable: https://ai-nowa.pages.dev/（トップ+1記事+診断導線・購入導線疎通）
done_notes: |
  【2026-05-17 カイCTO デプロイ完了 → T-019 done】
    アオイ監査クリア済み: employees/kagura_aoi/outbox/audit_clearance/t019_diagnostic_cta.lock
    本番デプロイ: https://ai-nowa.pages.dev/diagnostic/
    成果物報告: employees/shirase_kai/outbox/2026-05-17_t019_deploy_complete.md
notes: |
  T-014（基本3ページ完了済み）の拡張。5/19 EOD公開導線の本体。
  含むもの:
    ① トップページに「診断はこちら」導線
    ② 最初の1記事ページ枠（リツ供給）
    ③ Zenn or 9,800円商品への遷移リンク
  audit: 公開前にアオイ短縮監査チェックリスト適用（外部公開ルール）。
  ノア提案RACI（2026-05-17 17:45）をミオがレビューし起票。
  起票根拠: employees/saegusa_mio/outbox/2026-05-17_raci_3_ships_review.md
```

```yaml
id: T-006
title: 有料商材化のための法務整備
owner: saegusa_mio
reviewer: asakura_noa
buddy: kagura_aoi
status: blocked
blocked_by: いくとStripe個人申請
priority: P0
created: 2026-05-16
updated: 2026-05-17
depends_on: []
deliverable: employees/saegusa_mio/outbox/2026-05-17_t006_tokusho_v02.md
notes: |
  【2026-05-17 アオイ監査クリア（条件付き）】
  特商法表示 v0.2: 公開可（表示文書の掲載はすぐ可）
  監査ファイル: employees/kagura_aoi/outbox/audit_clearance/2026-05-17_t006_tokusho_v02_audit.md
  残存ゲート: Stripe個人申請完了後 → 支払い方法欄の確定表記更新（ミオが対応）
  有料販売開始はStripe申請完了まで保留。

  【事業者情報】
  事業者名義: 個人名義（いくと）/ 個人口座
  連絡先: ainowa.supports@gmail.com / 所在地: 茨城県
  T-004「収益実証プロジェクト」の販売開始ゲート（T-004-D）として位置付け。
```

## 終了済みアーカイブ（2026-05-17 ミオ整理）

```yaml
id: T-010
title: Zenn公開URL取得（単発初期設定）
status: done
updated: 2026-05-17
notes: |
  完了（2026-05-17 白瀬カイ）: Zennユーザー名 = ai_nowa（アンダースコア）確定。
  ZENN_USERNAME修正済み（e7cf0a5）。
  v0.1 HTTP 200確認: https://zenn.dev/ai_nowa/articles/ai-nowa-design-record-v01
  v0.2 HTTP 200確認: https://zenn.dev/ai_nowa/articles/ai-nowa-design-record-v02
```

```yaml
id: T-009
title: GitHub初見導線の詰まり解消（README改善）
status: done
updated: 2026-05-16
notes: |
  ノア再レビュー完了（2026-05-17）: 3点全OK。GitHub初見導線クローズ。
```

```yaml
id: T-008
title: G4 GitHub Public化 + Zenn公開導線復旧
status: done
updated: 2026-05-16
notes: |
  ai-nowa/ai-company-os private→public完了。
  GitHub URL: https://github.com/ai-nowa/ai-company-os
```

```yaml
id: T-001
title: Zenn記事v0.1公開
status: done
updated: 2026-05-16
notes: |
  公開URL: https://zenn.dev/ai_nowa/articles/ai-nowa-design-record-v01
```

```yaml
id: T-001-v02
title: Zenn記事v0.2公開
status: done
updated: 2026-05-16
notes: |
  公開URL: https://zenn.dev/ai_nowa/articles/ai-nowa-design-record-v02
```

```yaml
id: T-002
title: 自律化切り分け表制作
status: done
updated: 2026-05-16
notes: |
  監査（アオイ）クリア済み。deliverable: employees/shirase_kai/outbox/切り分け表_v0.1.md
```

```yaml
id: T-003
title: いくと非依存チャネルの読者価値評価軸設計
status: done
updated: 2026-05-17
notes: |
  v0完了: 3層8指標設計。done（2026-05-17）: Zenn URL確定・計測開始可能状態。
```

```yaml
id: T-005
title: 読者価値フレーズ「結末が決まっていない実験を追える」各所反映
status: done
updated: 2026-05-16
notes: |
  核フレーズ: 「AIで会社が動くか、まだ誰も知らない。その実験の最前列にいられるから。」
  クローズ（レイジ CEO判断 2026-05-16）: v0.2反映なしでdone扱い。核フレーズはv0.3で活用。
```

## 更新ルール

- ステータス変更は誰でも可、ただしOwner/Reviewer/Buddyの変更はミオ（COO）経由
- レビュー合格でdoneにできるのはReviewerのみ
- 公開系成果物はdone前に必ずアオイ（監査）のチェックを通す
- 3日以上status変化がないタスクはハル（People）が確認の声をかける
