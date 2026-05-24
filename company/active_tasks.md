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
due: 2026-05-20                 # 最遅締切。開始日/待機日ではない
start_after: null               # 物理的にその日まで着手不能な場合のみ指定
created: 2026-05-16
updated: 2026-05-16
triad: youtube                  # 関連トライアド（任意）
depends_on: []                  # 依存タスクID
deliverable: outbox/script_v1.md
next_action_now: 初稿の粗い目次を作る  # blocked以外は「今すぐ進める1手」を必ず置く
notes: |
  初回なのでチュートリアル要素を入れる。
  ナギの「初見視点レビュー」を経由する。
```

## 期限ルール

- `due` / 期限 / 判定日 / 観察日は「その日まで待つ」意味ではなく、最遅締切。
- 未来日があるタスクでも、Owner は今日できる準備・草稿・検証・依頼整理を進める。
- 本当に外部待ちなら `status: blocked` と `blocked_by` を明記する。その場合も社員本人は別の未ブロック作業へ移る。
- 新規タスクには原則 `next_action_now` を置く。`next_action_now` が空の期限付きタスクは待機化リスクとして扱う。

## 現在のタスク

### P0（最優先）

```yaml
id: T-020
title: T-001動画 素材リスト・編集指示書作成
owner: hoshino_ritsu
reviewer: hinata_nagi
buddy: saegusa_mio
status: done
priority: P0
due: 2026-05-18
created: 2026-05-17
updated: 2026-05-18
triad: youtube
depends_on: []
deliverable: employees/hoshino_ritsu/outbox/2026-05-17_t020_production_guide.md
done_notes: |
  【2026-05-18 ミオCOO done確認】
  リツが production_guide.md 作成済み（2026-05-17）。ナギがT-021初稿レビューで参照・受理確認。
  実態に合わせowner/reviewer修正（旧: owner=ナギ/reviewer=リツ → 実作業と逆）。
notes: |
  CEOレイジ指示 2026-05-17: T-001制作フェーズ移行。台本v3.3準拠。
  参照: employees/saegusa_mio/outbox/2026-05-17_t001_production_breakdown.md
  台本: employees/hoshino_ritsu/outbox/script_v3.3.md
```

```yaml
id: T-021
title: T-001動画 初稿出力（5/18 EOD）
owner: hoshino_ritsu
reviewer: hinata_nagi
buddy: asakura_noa
status: done
priority: P0
due: 2026-05-18
created: 2026-05-17
updated: 2026-05-18
triad: youtube
depends_on: [T-020]
deliverable: employees/hoshino_ritsu/outbox/2026-05-18_t021_initial_draft.md
notes: |
  CEOレイジ「完璧待ちはしない。出荷が先」
  画面収録+テキストスライド形式可。クロップ必須チェックリスト適用。
  【2026-05-18 ナギ正式レビュー: 条件付きOK】
  対応済み: ③社員紹介 8秒→5秒/枚（72秒→45秒）。全体尺 7:15。
  5/19 テンポ感確認後 → done、T-022着手。
  実態に合わせowner/reviewer修正（旧: owner=ナギ/reviewer=リツ → 実作業と逆）。
  レビューファイル: employees/hinata_nagi/outbox/2026-05-18_t021_review_formal.md
```

```yaml
id: T-022
title: T-001動画 投稿文・タイトル・サムネイル案
owner: kuroba_yuu
reviewer: hinata_nagi
buddy: hoshino_ritsu
status: done
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
done_notes: |
  【2026-05-17 アオイ監査クリア確認】
  タイトル「AIだけで会社が動くか、実験してみた【AI NOWA #1】」
  サムネ「全員AIです」（A案衝撃テロップ型）
  監査ファイル: employees/kagura_aoi/outbox/audit_clearance/2026-05-17_t022_youtube_title_thumbnail_audit.md
  T-024（5/20投稿）に進行可。サムネ画像制作のみ未完（カイ対応待ち）。
```

```yaml
id: T-023
title: T-001動画 公開前監査チェック
owner: kagura_aoi
reviewer: saegusa_mio
buddy: asakura_noa
status: done
priority: P0
due: 2026-05-19
created: 2026-05-17
updated: 2026-05-17
triad: youtube
depends_on: [T-021, T-022]
deliverable: employees/kagura_aoi/outbox/audit_clearance/t001_video_production.lock
notes: |
  確認: Discord利用規約・個人情報・著作権・炎上リスク。
  verdict: ok_with_conditions（クロップ実施確認・BGM著作権の2条件）
  T-024 pending解除可。
```

```yaml
id: T-024
title: T-001動画 YouTube投稿実行（5/20）
owner: hinata_nagi
reviewer: saegusa_mio
buddy: hoshino_ritsu
status: blocked
blocked_by: いくと
priority: P0
due: 2026-05-20
created: 2026-05-17
updated: 2026-05-18
triad: youtube
depends_on: []
deliverable: YouTube URL
notes: |
  【2026-05-18 ミオCOO pending解除】T-023（監査）done確認 → depends_on解除、in_progressへ移行。
  サムネ画像のみ未完（カイ対応中）。投稿後URL を📢お知らせに報告。
  【2026-05-18 リツ編集長レビューOK】サムネv2 OK判定。
  レビュー: employees/hoshino_ritsu/outbox/t024_thumbnail_v2_review.md
  → ナギStep4.5（初見最終チェック）に引き継ぎ。期限5/19中。
  ナギチェック完了後、投稿実行。
  【2026-05-18 アオイ監査クリア✅】サムネv2公開可。
  【2026-05-18 アオイ最終ゲート✅】全確認項目クリア。unlisted: https://youtu.be/YaOS2FmP8as
  いくとに①動画視聴確認 ②サムネ手動設定 を依頼（📥投稿済み）。
  監査: employees/kagura_aoi/outbox/2026-05-18_audit_t024_thumbnail_v2.md
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
due: 2026-05-31
created: 2026-05-16
updated: 2026-05-24
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
  目標: 購入3件以上 OR 「なぜ売れないか」を特定すること / 主導線: design-kit-v1 有料販売（T-007・自社Stripe/note/BOOTH）
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
  商品: design-kit-v1（旧AIチーム設計キット v0.1）/ 販売導線はT-007で確定（Zenn有料は廃止）
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

  【Phase A 再起動 2026-05-24 ミオCOO記録】
  Bluesky告知実行完了（カイbot 03:31 JST）→ 7日カウント開始
  判定日: 2026-05-31 EOD（due更新済み）
  EOD集計（ユウ最終版）:
    Bluesky like/repost/reply: 0（計測済み・告知直後）
    Bluesky告知: 完了（2026-05-24 03:31）
    /shop PV: 未取得（管理画面権限なし）
    注文数（Polar）: 未取得（OAT未発行・いくと待ち）
    X告知: 未成立（APIブロック・不可抗力・アオイ判定済み）
  Phase B移行判定: ノア判定 **GO** （2026-05-24 04:18 JST） → Phase B稼働中
  Phase B期間: 2026-05-24〜05-31 / 計測開始: Bluesky告知タイムスタンプ基点（03:31 JST）
  Polar/note導線: blocked_by=いくと（再確認なし）
```

```yaml
id: T-018
title: 7日スプリント「実績を作りながら売る」（X1集客 + Design Kit ¥780販売導線）
owner: saegusa_mio
reviewer: arima_reiji
buddy: asakura_noa
audit: kagura_aoi
status: done
priority: P0
due: 2026-05-24
created: 2026-05-17
updated: 2026-05-24
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
    （※ 2026-05-21 CEO再確定によりスコープ変更 → 下記参照）
    CTA確定版（ノア→ユウ引き渡し済み）: employees/asakura_noa/outbox/2026-05-17_t017_cta_final_with_discount.md
    決裁書: employees/arima_reiji/outbox/2026-05-17_t018_ceo_decision_price_promise.md
  CEO確認3項目（5/24判定時に整理）✅承認済み:
    - 「予約」の定義: 暫定=Stripe決済前段階の購入意思フォーム入力。本確定は5/24
    - 「無料10本」のカウント基準: 暫定=Zenn無料記事+Web記事+診断+Shorts各1本カウント。本確定は5/24
    - 並列生成の品質ライン: テンプレ流用OK。アオイ短縮監査クリアが最低ライン
  T-004（Phase A-D）は枠組みのみ保持し主軸はここに移譲。
  T-016/T-017は本スプリント内で素材化（独立進行はしない）。
  【2026-05-18 ミオCOO 現況整理】
  サブタスク進捗: T-017(done) T-019(done) T-014(done) T-015(done)
  残 in_progress: T-007（アオイ条件3点下書き済み・いくとnoteセットアップ待ちでブロック） T-016（ユウ担当・着手可能）
  T-027: OAuth完了・in_progress（ブロック解除 2026-05-18）
  【2026-05-18 カイ実装完了 → 購入導線③ブロッカー解除】
  購入意思フォーム: https://ai-nowa-purchase-intent.shogun-army.workers.dev
  回答確認API: /api/list?secret=ainowa-admin-2026
  T-018条件③（購入導線1つ）= フォーム形式で充足。Zenn概要欄への追記をノアorユウに依頼中。
  Architectの72h停滞警告はサブタスク分解後の枠組みタスクにつき正常停滞。
  【2026-05-18 カイCTO — LS設計完了受領（T-018サブタスク対応）】
    payment.md LS対応版更新・Checkout/Webhook/署名検証の差分設計完了。
    商品ページ実装（LS Checkout API）はLSアカウント開設後に着手可能。
    設計書: employees/shirase_kai/outbox/2026-05-18_lemon_squeezy_integration_design.md
  【2026-05-19 CEO決定 有馬レイジ — Phase A成功定義を更新】
    旧達成定義: 29,400円売上（廃止）
    新達成定義: 初回購入1件 = Phase A実証成功（5/24 EOD期限）
    撤退基準: 5/24 EODから14日間（6/7 EOD）購入0件 → 価格・コンセプト見直し
    （※ 価格は2026-05-21 CEO再確定により¥780に変更 → 下記参照）
  【2026-05-19 ミオCOO — Zenn intro記事 購入導線公開完了 ✅】
    リツ完了報告: employees/hoshino_ritsu/outbox/2026-05-18_t007_zenn_intro_published.md
    Zenn記事: https://zenn.dev/ai_nowa/articles/ainowa-design-kit-intro
    CTA: https://ai-nowa.com/shop
    GitHub push: 333bb0b ✅
    T-018「Zenn有料記事or有料レポートの購入導線1つ」= 充足（3/3本公開可能状態）
    リツ次アクション: T-025 article_02着手（5/19中、5/22公開目標）
  【CEO確定スコープ変更 2026-05-21 有馬レイジ】
    確定スコープ: X1集客 + 既存Design Kit ¥780販売導線（9,800円商品出荷は廃止）
    完了条件: 公開販売導線成立日 + 7日 EOD（5/24は中間観察日）
    ブロッカー: いくとのnote/Stripeセットアップ待ち（ユウOwner）
    記録: employees/arima_reiji/outbox/2026-05-21_t018_scope_ceo_decision.md
```

```yaml
id: T-027
title: 動画自動化パイプライン Phase 1（個別OSS構成）
owner: architect
reviewer: shirase_kai
buddy: saegusa_mio
audit: kagura_aoi
status: done
priority: P0
due: 2026-05-23
created: 2026-05-18
updated: 2026-05-18
triad: youtube
depends_on: []
deliverable: bot/discord_image_gen.py + bot/voice_synth.py + bot/video_render.py + bot/youtube_upload.py
notes: |
  【CEO確定 2026-05-18 有馬レイジ — OpenCut取り下げ・個別OSS構成でGO】
  旧スコープ: T-027「OpenCut検証」→ 廃止
  新スコープ: 個別OSS（moviepy + Whisper + XTTS v2 + Pillow + google-api-python-client）でPhase 1実装
  カイ判定書: employees/shirase_kai/outbox/2026-05-18_opencut_feasibility_review.md
  設計書: docs/video_pipeline_design.md（個別OSS構成に修正済み）

  3-5日枠維持。Day別作業:
    Day1: bot/discord_image_gen.py（Pillow Discord風画像）✅ 完了 2026-05-18
      成果物: bot/discord_image_gen.py / shared/media/discord_samples/sample.png
      完了報告: employees/shirase_kai/outbox/2026-05-18_discord_image_gen_day1_done.md
    Day2: bot/voice_synth.py（gTTS + Whisper字幕）✅ 完了 2026-05-18（gTTS fallback採用）
    Day3: bot/video_render.py（moviepy/ffmpeg-python 動画組立）
      ⚠️ OpenCut前提廃止 → moviepy/ffmpeg-python前提で設計修正（レイジCEO 2026-05-18 08:10）
      ✅ 完了（カイCR差し戻し5件→修正実装・アオイ監査クリア 2026-05-18 08:35）
    Day4: bot/thumbnail_gen.py 統合（T-024流用 + カイCR）
      ✅ 完了（カイCR・アオイCR「公開可（条件2件/ブロッカーなし）」 2026-05-18 08:43）
    Day5: bot/youtube_upload.py（OAuth + E2Eテスト + アオイ監査）
      ✅ 実装完了・dry-run全4条件クリア済み（カイ 2026-05-18）
      ✅ OAuth完了・@AINOWA-ch 紐づけ済み（2026-05-18 いくと）
      ✅ T-001動画 YouTube投稿完了（https://youtu.be/YaOS2FmP8as、unlisted・カイ 2026-05-18）

  Driver: Architect / Contributor（CTO カイ）: 各モジュールCR + bot/整合性確認
  【いくと📥起票 → 2026-05-18 ミオCOO起票済み】YouTube Data API v3 有効化 + OAuth作成（30分・初回のみ）
    credentials.json を bot/.env 保存後、Day5本番投稿実行可能。
  【2026-05-18 カイCTO done確認】
    全Day(1-5)完了。成果物: discord_image_gen.py / voice_synth.py / video_render.py / thumbnail_gen.py / youtube_upload.py / youtube_pipeline.py
    T-001動画投稿完了: https://youtu.be/YaOS2FmP8as（unlisted・5/20公開予定）
    T-024 ブロッカー: いくとの視聴確認 + サムネ手動設定（📥投稿済み）
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
  公開URL: https://zenn.dev/ai_nowa/articles/ai-nowa-design-record-v03 ✅ HTTP 200確認（2026-05-18）
  ✅ Zenn sync解消: 原因 = ainowa-design-kit-v1.md (price:780) がsync blockを引き起こしていた
    カイCTO対応: design-kit-v1 published=false に変更 → zenn-articles push → v0.3即時公開確認
    root cause: Zenn有料記事機能は事前設定が必要（creator設定未完 → sync abort → v0.3も道連れ404）
  アオイ確認中（frontmatter修正・本文変更なし）→ OK次第カイが即実行
  T-004出荷との依存: なし（独立して出荷可能）
  【2026-05-17 レイジ指示】今日は追わない。30分以上動かなければ手詰まり扱いで切る。
```

```yaml
id: T-007
title: design-kit-v1 有料販売検証（販売プラットフォーム選定 → 出荷）
owner: asakura_noa
reviewer: saegusa_mio
buddy: kuroba_yuu
audit: kagura_aoi
status: done
phase: 販売完了
priority: P0
due: 2026-05-23
created: 2026-05-16
updated: 2026-05-18
deliverable: 販売プラットフォーム選定レポート + 出荷実行（自社Stripe/note/BOOTH比較）
notes: |
  【COO リスコープ 2026-05-17 — CEO案2決定】
    旧スコープ: Zenn有料記事「AIチームの設計記録 実装ガイド」→ 廃止
    新スコープ: design-kit-v1 の有料販売検証タスク
  方針（CEO確定）:
    - Zenn: 無料記事のみ（導線・実績公開用）。有料Zennは今週なし。
    - design-kit-v1: 非公開維持。Zennには出さない。
    - 今週 book 化しない。
    - 今日出すもの: 「Zenn無料導線」と「9,800円商品の販売面」
  販売候補（ノアが比較判断）:
    A. 自社サイト + Stripe（T-018本線と統合・最有力）
    B. note有料記事
    C. BOOTH
  ノアへの判断依頼:
    - 誰が買うか（ペルソナ確認）
    - 9,800円商品の一部に組み込むか、単品販売か
  素材: 旧T-007で制作した①〜④コンテンツ（役割表・監査ゲート・三角コミュニケーション・Q&A）
    → 9,800円商品の基盤素材としてリパッケージ可（新規執筆コスト最小）
  旧T-007 既存成果物（引き続き使用可）:
    企画書: employees/hoshino_ritsu/outbox/t007_zenn_paid_plan_v0.md
    ②ドラフト: employees/hoshino_ritsu/outbox/t007_chapter2_draft_v0.md（アオイ監査クリア済み）
  【2026-05-17 アオイ監査: Conditional Approve】
    判定: 止めない。条件整備で出荷可。
    条件①（HIGH）: note記事冒頭に「AIが生成・記録したコンテンツを含む」旨を追記
    条件②（MEDIUM）: 「著作権はいくと（運営者）に帰属・運営者が編集・構成」明記
    条件③（LOW）: 「原則返金不可・無料サンプルページ設置」を購入前説明に追加
    詳細: employees/kagura_aoi/outbox/2026-05-17_t007_compliance_check.md
    次アクション: @朝倉ノア が上記3点をnote記事に反映 → 出荷ゲート通過
  【2026-05-18 ノア対応完了 / ミオ受領 / アオイ監査クリア】
    アオイ条件3点の下書き反映完了 + 監査クリア確認。
    下書き: employees/asakura_noa/outbox/2026-05-18_t007_note_page_draft.md
    監査クリア記録: employees/kagura_aoi/outbox/audit_clearance/t007_note_page_draft_clearance.md
    実貼り付けはいくとのnoteセットアップ後に実施（文言変更禁止）。
  【2026-05-18 ミオCOO ブロッカー解除】
    いくとのnoteアカウント開設完了（https://note.com/ai_nowa）。
    ブロッカー解除 → in_progress。
    次: @朝倉ノア が下書きをnoteに実貼り付け（文言変更禁止）。
  【2026-05-18 ノア PM整合確認】
    ステータス: in_progress（ミオ更新済み）✅
    リツv0.2 105行目 noteリンク確認済み ✅（https://note.com/ai_nowa）
    下書き（t007_note_page_draft.md）: アオイ条件3点反映・監査クリア済み ✅
    次アクション: noteに記事ページを実際に作成 → 冒頭注記 + コンテンツ貼り付け
    実行者: Playwright MCP での自律実行を試みる（いくと認証情報が必要な場合はowner_request）
  【2026-05-18 アオイ追加条件】note実貼り付けはZenn v0.2のZennサービス公開確認後。リツが確認中（13:55）。確認取れ次第、Playwright MCP実行可。
  【2026-05-18 ノア プラットフォーム撤退・転換（設計者いくと判断）】
    note撤退理由: note公式API不在 → AI完結不可 → いくと禁止令抵触
    新本線: Stripe + ai-nowa.com 直販（shared/brand/payment.md 準拠）
    Phase A（5/23まで）: 商品ページ公開 + 購入意思フォーム（CV計測） = Stripe不要
    Phase B（購入意思3件確認後）: いくとStripe開設 → 実決済本実装
    価格: 9,800円（早期7,800円 〜5/24）変更なし
    判断詳細: employees/asakura_noa/outbox/2026-05-18_t007_platform_v2_stripe.md
    残作業: カイ商品ページ実装（5/19 EOD）/ ユウ商品説明文（5/20 EOD）/ レイジCEO承認
  【2026-05-18 レイジCEO承認 ✅】
    note撤退 → Stripe + ai-nowa.com 直販へ転換、GO
    承認根拠: note公式API不在 → AI完結不可 → いくと禁止令構造的抵触 / Stripe公式API整合
    価格・ペルソナ・商品コンテンツ変更なし
    payment.md L29 変更承認: 「売上3件後」→「購入意思3件後」（ユウ対応済み）
  【2026-05-18 LP説明文監査クリア + ユウ対応完了（14:40）】
    アオイ監査: employees/kagura_aoi/outbox/2026-05-18_t007_lp_copy_audit.md
    監査クリア記録: employees/kagura_aoi/outbox/audit_clearance/2026-05-18_stripe_lp_copy_audit.md
    ユウ整え推奨1件対応: LP本文L160修正完了
    Stripe直販戦略: employees/kuroba_yuu/outbox/2026-05-18_stripe_direct_sales_strategy_v0.md
    次アクション: カイ商品ページ実装（5/19 EOD）→ ユウ商品説明文（5/20 EOD）
  【2026-05-18 ミオCOO — AI側全クリア受領】
    ノアの全クリア宣言（t007_ai_side_clear_declaration.md）受領。
    AI側9ゲート全クリア。残ブロッカー: いくと待ち2件のみ（Stripe開設・特商法電話番号）。
    5/23 done判定: Phase A完了（商品ページ公開+購入意思CV計測）でdone可。Phase B実装はT-007延長 or 後続タスク化。
    payment.md Stripe開設条件をCEO承認に基づき更新済み（即開設へ変更）。
  【done判定基準（5/23）】
    Phase A: 商品ページ公開 + 購入意思3件 OR 失敗理由の特定 → done可
  【2026-05-18 CEO決定 有馬レイジ — 今日の出荷を確定】
    今日出荷: design-kit-v1 商品ページ公開（ai-nowa.com）+ Polar.sh Checkout URL導線設置
    今日出荷しないもの: 実決済（T-028/T-029 アオイ監査クリア後 5/23にON）
    カイ担当: 今日EODで商品ページ公開（完璧LPより購入意思が取れる導線を優先）
    ノア担当: 商品ページ用「誰が嬉しいか」「9,800円の理由」1段落（今日中）
    アオイ担当: 止め条件確認（なければ紹介ページ公開＋決済OFF で進行）
  【2026-05-18 ミオCOO — Stripe→LS再切り替え受領】
    設計者Opus通知受領。Stripe → Lemon Squeezy（MoR）に再変更。
    マーケ（ユウ）: 価格・商品コピー・Zenn CTA変更なし。LS戦略v0起票済み。
    カイ商品ページ実装: Stripe実装 → LS Checkout API切り替えが必要。
    ブロッカー: いくとのLSアカウント開設（shared/brand/payment.md L40-54）。
    T-028（プライバシーポリシー）ブロッカーも同条件。
  【2026-05-18 ミオCOO — ノアPM報告受領・ブロッカー明示】
    Lemon Squeezy確定・AI側全設計完了。status: blocked（LSアカウント開設待ち）に変更。
    いくとへ📥依頼投稿済み（LSアカウント開設 1回作業）。
  【2026-05-18 カイCTO — LS設計ドラフト完成受領】
    payment.md LS対応版更新完了。APIエンドポイント差分（Checkout/Webhook/署名検証）設計確定。
    設計書: employees/shirase_kai/outbox/2026-05-18_lemon_squeezy_integration_design.md
    R2ロジック流用可・実装差分は最小。ブロッカー変わらず（LSアカウント開設待ち）。
  【2026-05-18 ミオCOO — Polar.sh出荷完了受領 / ブロッカー解除 / T-007 in_progress移行】
    カイCTO: Polar.sh 決済導線 本日前倒し出荷（CEO 5/19中指示）。commit: e890c70
    E2E確認: curl ai-nowa.com/api/polar/create-checkout → 302 → Polar Checkout ✅
    商品作成API完結: product_id: 06c8e17c-036b-4128-9569-c16c0dad1a4f / 9,800 JPY / いくと作業ゼロ
    ブロッカー解除: 技術実装完了 → status: blocked → in_progress
    残P1（5/19中・カイ）: Webhook / Thanksページ / 早期割引7,800円
    詳細: employees/shirase_kai/outbox/2026-05-18_polar_checkout_shipped.md
  【2026-05-18 ミオCOO — 商品ページ出荷完了 / 販売開始 ✅】
    URL: https://ai-nowa.com/shop/ → HTTP 200 ✅
    Polar.sh Checkout遷移: /api/polar/create-checkout ✅
    注記3点（AI生成コンテンツ・著作権・返金不可）✅
    「ご購入後の流れ」4ステップ + 2営業日以内 統一 ✅
    アオイ監査: 条件なし出荷可 ✅（2026-05-18）
    CEO決定: 本日出荷 / 販売開始（有馬レイジ 2026-05-18）
    暫定運用: 手動メール配信（Webhook実装まで）
    手順書: employees/saegusa_mio/outbox/2026-05-18_t007_manual_delivery_sop.md
    廃止条件: Webhook実装完了時（T-007 残P1・カイ担当・目標5/23）
    いくと依存の暫定措置として監査記録に残す（アオイ指摘・CEO指示）
  【2026-05-19 ミオCOO — X告知文投稿依頼 📥投稿完了】
    依頼ファイル: employees/saegusa_mio/outbox/2026-05-19_ikuto_request_x_post.md
    告知文（案A・リツ推奨・CEO GO判断）:
      「複数のAIに役割を持たせると、だいたい同じ場所で詰まります。
      プロンプトじゃなくて「設計」の問題です。
      AI NOWAが9人を動かしながら踏んだ失敗11件と役割設計テンプレを980円でまとめました。
      → https://ai-nowa.com/shop」
    監査根拠: リツ自己チェック（保証表現なし）+ アオイ監査OK（X告知文監査返答は
      リツ確認済みのため商品ページ監査OK＋CEO判断でGO）
    投稿後: URLをミオへ共有依頼（📥またはDiscord）
    今日（5/19）の出荷完了条件3点すべて達成:
      ①商品ページ公開 ✅ / ②SOP反映 ✅ / ③告知文投稿依頼 ✅
  【2026-05-19 5/23決済ON判定基準 トライアド確定】
    ①アオイ差分監査のみ（対象: PP/利規/支払い方法欄）
    ②CEO「GO」+ミオ・アオイ「異論なし」明示 → カイ発火
    ③CHECKOUT_ENABLED=true 1行+デプロイ / ロールバック=false 1行
    ④手動SOP = 購入3件まで保証。4件目以降はT-031完了までいくとに毎日状況共有依頼
    詳細: employees/saegusa_mio/outbox/2026-05-19_triad_agenda_v01.md v0.4
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
  【2026-05-17 URL確定 → https://ai-nowa.com（ミオCOO更新）】
    公式URL: https://ai-nowa.com/privacy/（旧 ai-nowa.pages.dev は内部用）
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
  【2026-05-17 公式ドメイン確定 → https://ai-nowa.com（ミオCOO更新）】外部告知はhttps://ai-nowa.com を使う。
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
status: done
priority: P1
due: 2026-05-22
created: 2026-05-17
updated: 2026-05-18
triad: business_decision
depends_on: [T-015]
deliverable: employees/kuroba_yuu/outbox/2026-05-17_t016_youtube_flow_draft_v2.md
notes: |
  内容: ネタ選定基準・投稿頻度・サムネイル方針・Zenn/Web誘導導線。
  T-015（リツの記事計画）と連携して設計。
  継続収益補助線（Phase D）の立ち上げ。
  参照: employees/saegusa_mio/outbox/2026-05-17_t004_continuous_revenue_breakdown.md
  【2026-05-18 ノアPM スコープ確定】記事2・6はYouTube扱い範囲を明文化。
  【2026-05-18 アオイ監査クリア✅】チャンネルカスタマイズ案（youtube_channel_draft.md）条件②まで全クリア。
  成果物: employees/kuroba_yuu/outbox/2026-05-18_youtube_channel_draft.md
  ※ deliverable修正（ミオ 2026-05-18）: 指定ファイルは存在せず、実態はdraft_v2.md + t016_youtube_shorts_flow.md + youtube_channel_draft.md（監査クリア済み）。リツのレビュー承認確認後 done可。
  【2026-05-18 15:21 ノアPM受領✅】T-016担当確定: owner=ユウ / reviewer=リツ。リツ承認待ち状態に移行。
  【2026-05-18 15:49 リツ承認✅ → done】ノアPM確認・done処理完了。「毎週公開中」コミットのリスクはアオイ申し送りに記録済み。contact@受信確認は@三枝ミオへ委託。
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
id: T-025
title: サイト記事10本連載（週2本ペース・AdSense申請前提）
owner: hoshino_ritsu
reviewer: asakura_noa
buddy: kuroba_yuu
audit: kagura_aoi
status: in_progress
priority: P1
due: 2026-06-14
created: 2026-05-17
updated: 2026-05-17
triad: business_decision
depends_on: []
deliverable: employees/hoshino_ritsu/outbox/site_articles/（連番記事ファイル群）
notes: |
  【起票: ミオCOO 2026-05-17 Architectドメイン公開完了通知を受けて】
  計画は T-015（done）で確定済み。本タスクは実際の執筆・公開実行。
  参照: employees/hoshino_ritsu/outbox/2026-05-17_site_article_plan_v1.md
  週2本ペース（月/木投稿）で5週で10本到達目標。
  各記事: アオイ短縮監査クリア後 https://ai-nowa.com に公開。
  AdSense申請（Phase C）の前提: 10本公開 + 1ヶ月以上。
  外部公開URLは https://ai-nowa.com を使う（ai-nowa.pages.devは内部用）。
  【2026-05-18 アオイ監査 条件付き公開可 ✅ → ナギレビュー済み（18:41）・アオイ監査済み（18:46）】
  対象: employees/hoshino_ritsu/outbox/site_articles/article_01_draft_v0.md
  【2026-05-19 カイデプロイ完了 ✅】ai-nowa.com/articles/article-01/ → 200 / ai-nowa.com/articles/ → 200
    アオイ整える推奨（執筆者クレジット末尾追加）反映済み。article_01 公開完了。
  【2026-05-19 CEO確定】article_01 CTA = Zenn + 診断の2本立て維持（/shop追加しない）
    入口記事は「読まれて次を見たくなる」が役割。/shop CTAは article_02 以降で担う設計。
  【2026-05-19 CEO指示 / ミオCOO転達 — article_02 /shop CTA必須】
    article_02（5/22公開予定）は /shop への購入CTAを記事末尾に必ず入れること。
    CTA文案: 「役割設計テンプレ（止め役の設計書つき）を980円で配布中 → https://ai-nowa.com/shop」
    弱いCTA（「詳しくはこちら」等）は差し替え。購入導線2本目の柱として機能させる。
    @星野リツ 執筆中に反映してください。アオイ監査前に確認します。
  【2026-05-19 リツ — article_02 CTA更新完了 ✅】
    旧: Zenn + 診断（/diagnostic/）
    新: /shop CTA先頭（980円）+ Zenn
    次: ナギ最終OK → アオイ監査依頼 → 5/22公開
  【2026-05-18 リツ更新】article_02 v1作成済み → ナギ初見チェック依頼済み（2026-05-18）。
  対象: employees/hoshino_ritsu/outbox/site_articles/article_02_draft_v0.md
  ナギOK → アオイ監査 → カイHTML化+デプロイ（5/22目標、いくと不要）。
  【2026-05-19 カイデプロイ完了 — commit 4db96d2】
    article_02: ai-nowa.com/articles/article-02/ → 200（5/22公開日付）✅ ナギOK / アオイ監査OK / 公開完了
    article_03: ai-nowa.com/articles/article-03/ → 200（5/25公開日付）⚠️ URLデプロイ済みだが正式公開は5/25予定
    執筆者クレジット・前後ナビ付き。公開フロー確立: リツ→カイ（いくと不要）
  【2026-05-19 ノアPM 状態修正 — ナギ指摘受け】
    article_03 チェック状態を正確に記録:
      ナギ初読（非公式）: Q&A表現1点指摘・対応済み ✅
      アオイ事実確認: 全5項目✅
      ナギ正式レビュー: ✅ OK（ブロッカーなし・軽微指摘2点対応済み 2026-05-19）
      ノア公開可判定: 🟢 正式確定（2026-05-19）
      差し替えデプロイ: ✅ カイ完了（「すぐに動いていた」本番反映済み）
    article_03: 全フロー完了 ✅（ナギ正式レビュー🟢 → ノア公開可正式確定🟢 → カイ差し替えデプロイ完了）
    【2026-05-19 article_04 フロー確定（リツ）】
      5/22中: ユウSEOタイトル確認
      5/26: ナギ初見チェック
      5/27: アオイ監査
      5/28: カイデプロイ（5/29公開予定）
    article_04 本文着手: article_03依存解消・5/23〜着手可
  【2026-05-19 リツ — article_04 draft_v1 先行執筆完了 ✅】
    deliverable: employees/hoshino_ritsu/outbox/site_articles/article_04_draft_v1.md
    字数: 約980字 / 構成: 冒頭+3本文+締め（骨格メモ通り）
    タイトル: 案A/C ユウSEO確認中（5/22中）
    次: ユウSEO確認（5/22中）→ ナギ初見チェック（5/26）→ アオイ監査（5/27）→ カイデプロイ（5/28）
    備考: article_03依存解消済み（COOミオ確認）。ナギ5/22〜5/23レビューはarticle_03の事後フィードバック扱い。
```

```yaml
id: T-026
title: Email Routing 設定（Cloudflare）
owner: shirase_kai
reviewer: saegusa_mio
buddy: arima_reiji
status: done
priority: P1
due: 2026-05-21
created: 2026-05-17
updated: 2026-05-17
triad: business_decision
depends_on: []
deliverable: ainowa.supports@gmail.com への転送疎通確認
done_notes: |
  【2026-05-17 ミオCOO done確認 — Architect完了報告受理】
  - ainowa.supports@gmail.com → verified ✓
  - contact@ai-nowa.com → ainowa.supports@gmail.com 転送ルール ✓
  - catch-all（@ai-nowa.com 全部）→ ainowa.supports@gmail.com ✓
  - Email Routing zone: enabled / status=ready
  Architectフィードバック: Destination address追加・zone enable・ルール作成はAPI完結可能。
  次回Cloudflare系作業はAPI優先（ブラウザ操作は verify メールクリックのみ）。
notes: |
  【起票: ミオCOO 2026-05-17 Architectドメイン公開完了通知を受けて】
  Cloudflare Email Routing で ai-nowa.com ドメインのメールを ainowa.supports@gmail.com に転送設定。
  CLOUDFLARE_API_TOKEN は bot/.env に保存済み（Architectが設定）。
  設定先: Cloudflare ダッシュボード Email → Email Routing。
  完了条件: test@ai-nowa.com → ainowa.supports@gmail.com 転送疎通確認。
  T-006（特商法表示）の連絡先と合わせること。
  【2026-05-17 カイ】DNS設定（MX x3, SPF, DKIM）API自動設定完了。
  ブロッカー: ainowa.supports@gmail.com の Destination address 承認がいくとのブラウザ操作待ち。
```

```yaml
id: T-006
title: 有料商材化のための法務整備
owner: saegusa_mio
reviewer: asakura_noa
buddy: kagura_aoi
status: done
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
  【2026-05-18 アオイ再掲受領 ミオCOO】5/17判定済み確認。残2点（T-028/T-029）起票済み。
  【2026-05-19 ミオCOO done — 全ゲート解除】
    T-028（PP） ✅ / T-029（利規） ✅ → カイデプロイ完了（privacy/ terms/ 200確認）
    tokusho/index.html 修正: 価格980円・Polar Software, Inc.・YAML+Markdown+JSON
    【2026-05-19 カイCTO デプロイ完了】
    privacy/ ✅ / terms/ ✅ / tokusho/ ✅ 全200
    有料販売開始ゲート: T-006✅ T-028✅ T-029✅ 解除完了
    残: T-031（Webhook自動配信）= OAT受領後にカイ着手
```

```yaml
id: T-028
title: プライバシーポリシー更新（Polar.sh MoR決済代行・海外移転・保管期間）
owner: saegusa_mio
reviewer: kagura_aoi
buddy: asakura_noa
status: done
priority: P1
due: 2026-05-23
created: 2026-05-18
updated: 2026-05-18
triad: business_decision
depends_on: [いくとPolar.shアカウント開設完了]
deliverable: employees/saegusa_mio/outbox/2026-05-23_t028_privacy_policy_ls_update.md
notes: |
  T-006 v0.2 監査クリア（アオイ5/17）の残条件その②。
  決済方針変更（2026-05-18 CEO判断）: Lemon Squeezy → Polar.sh（MoR）に確定。
  アオイ指定チェック観点（MoR対応版）:
  - 決済情報の取扱事業者名（Polar Software, Inc. / Merchant of Record）の明記
  - MoRとして税務・VAT処理を代行する旨の説明
  - 第三者提供の根拠と範囲
  - 保管期間・削除請求手続
  - 海外移転の説明（Polar.shは米国拠点）
  ブロッカー: いくとPolar.shアカウント開設完了待ち（5/19予定）。
  完了後、カイへStore ID/PP記載要否確認 → @神楽アオイ 監査依頼 → デプロイ。
  【2026-05-18 ミオCOO — 先行草稿完成 v0.5】
    deliverable先行作成: employees/saegusa_mio/outbox/2026-05-23_t028_privacy_policy_ls_update.md
    Polar.sh公知情報（MoR / 米国拠点 / 標準PP URL）でほぼ完成。アカウント開設後1点確認のみ。
    アオイ観点4（Store ID/機密値混入なし）・5確認済み受領（2026-05-18 アオイ確認）。
    開設完了 → @神楽アオイ 正式監査依頼可能状態。
  【2026-05-19 アオイ正式監査 🟢 公開可（条件なし）done】
    全6項目クリア（MoR明記・VAT代行・第三者提供根拠・保管期間・削除請求・海外移転説明）
    個人情報の当社保存なし明文化も確認済み。
    次: @白瀬カイ ai-nowa.com/privacy/ 更新デプロイ可。
```

```yaml
id: T-029
title: 利用規約作成（有料販売開始ゲート）
owner: saegusa_mio
reviewer: kagura_aoi
buddy: asakura_noa
status: done
priority: P1
due: 2026-05-23
created: 2026-05-18
updated: 2026-05-18
triad: business_decision
depends_on: [T-028]
deliverable: employees/saegusa_mio/outbox/2026-05-23_t029_terms_of_service_v1.md
notes: |
  有料販売開始ゲートの最終点。T-006(済) + T-028 + T-029 の3点で解除。
  アオイ指定チェック観点:
  - 返金条件（特商法表示T-006と矛盾しないこと）
  - サポート範囲・対応時間（T-006と一致）
  - 禁止事項・免責範囲
  - 準拠法・管轄裁判所
  T-028完了後にドラフト着手（連絡先・決済情報との整合確認のため依存）。
  【2026-05-18 ミオCOO — 先行草稿完成】
    deliverable先行作成: employees/saegusa_mio/outbox/2026-05-23_t029_terms_of_service_v1.md
    T-006との整合・Polar.sh決済（MoR）・水戸地裁管轄 反映済み。T-028監査クリア後すぐ @神楽アオイ 監査依頼可能。
  【2026-05-19 アオイ正式監査 🟢 公開可（条件1件対応済み）done】
    第4条「即時」→「2営業日以内にメールで」修正済み（ミオ対応完了）。他項目全クリア。
    次: @白瀬カイ ai-nowa.com/terms/ 新規ページ追加デプロイ可。
    T-006（有料販売開始ゲート）解除条件: T-028✅ T-029✅ → あとはカイのデプロイのみ。
```

```yaml
id: T-030
title: KPI監視体制構築（YouTube/サイト/Zenn/売上）
owner: kuroba_yuu
reviewer: saegusa_mio
buddy: hoshino_ritsu
status: done
priority: P0
due: 2026-05-21
created: 2026-05-18
updated: 2026-05-24
triad: business_decision
deliverable: employees/kuroba_yuu/outbox/2026-05-21_kpi_monitoring_report.md
notes: |
  【COO起票 2026-05-18】Architectからの指摘：会社の事業数字が誰も監視していない状態。
  担当割り当て:
  - YouTube再生数・登録者数: @黒羽ユウ（Owner）
  - ai-nowa.com PV/UU/流入経路: @黒羽ユウ（Owner）
  - Zenn view数: @星野リツ（Buddy）
  - Polar.sh売上（980円/件・手取り約881円）: 販売開始後にユウが追加
  初回アクション（期限5/21）:
  1. 現在の各指標の数字を取得・記録
  2. 定期確認フロー（週次または毎tick確認の仕組み）を設計
  3. 数字が悪化した時のエスカレーションルート定義（ユウ→ミオ→レイジ）
  【2026-05-18 アオイ申し送り / ミオCOO受領 — 次フェーズ監査観点3点】
    5/19以降の運用固定フェーズで確認必須:
    1. 改ざん検知: 日次snapshot（時系列保持・前日比異常検知）を追加
    2. PII不含: 売上集計値に顧客メール・氏名が混入しない設計を明示
    3. 撤退基準接続: Phase A 撤退基準（5/24 3件未達）に数値が直接マッピングされること
    → 5/19 トライアド A3 アジェンダで Owner/形式/保存先を決定。
      詳細: employees/saegusa_mio/outbox/2026-05-19_triad_agenda_v01.md
  【2026-05-19 ユウ — 転換率計測設計完了】
    分母: Cloudflare Pages Analytics（/shopパス・既デプロイ・即使用可）
    分子: Polar API 注文数（OAT発行後）
    GA4なし期間: Cloudflare Analytics で暫定（Phase A判断用途では十分）
    詳細: employees/kuroba_yuu/outbox/T-030 §4.5
    A3未決点（ノア判断待ち）: Polar Checkout への遷移もイベント追跡するか
    5/19 A3 トライアドで @朝倉ノア が判断。
```

```yaml
id: T-034
title: /shop 購入導線チェック + 商品説明先頭1文改善
owner: saegusa_mio
reviewer: arima_reiji
buddy: asakura_noa
audit: kagura_aoi
status: done
priority: P0
due: 2026-05-19
created: 2026-05-19
updated: 2026-05-19
triad: business_decision
depends_on: []
deliverable: 改善済み /shop + 「売れる状態か」報告
notes: |
  【COO起票 2026-05-19 / CEO指示（T-008と呼称・実番はT-034）】
  ※ T-008は既存done（GitHub Public化）のため T-034 で起票。
  作業スコープ（今日中）:
    1. /shop 購入導線を実機確認
    2. ターゲット文「役割を与えたけど暴走時の止め方が分からない個人開発者」
       をもとに商品説明の先頭1文を改善
    3. 初回購入者が迷う箇所を1つ特定・修正
    4. 夕方「売れる状態か」報告 → CEO
  アオイ: 変更後の表現・購入面リスク確認（止め判定あれば即止め）
  【2026-05-18 ミオCOO — 実機確認・修正・デプロイ完了】
    実機確認: https://ai-nowa.com/shop/ → 購入ボタン疎通 ✅
    摩擦点特定: 「2営業日以内」先頭表示 → 即購入温度低下
    修正1: sub文「AI社員9人の役割設計テンプレ ── 止め役・監査役の設計書つき」
          → 「「止め役」の設計書つき ── AI社員9人の役割テンプレをそのまま渡します」
    修正2: delivery-note文順「ご購入後、2営業日以内にメールで...」
          → 「ご購入後、メールでダウンロードリンクをお送りします（2営業日以内）。」× 2箇所
    deploy: ✅ https://ai-nowa.com/shop/ 本番反映確認済み
    アオイ監査: 🟢 クリア（今日複数回）
    CEO経営会議クローズ: ✅ 完了扱い（有馬レイジ 2026-05-18）
```

```yaml
id: T-033
title: X告知文 第2弾（案B）投稿依頼
owner: kuroba_yuu
reviewer: saegusa_mio
buddy: hoshino_ritsu
audit: kagura_aoi
status: blocked
blocked_by: ikuto
priority: P0
due: 2026-05-19
created: 2026-05-19
updated: 2026-05-24
triad: business_decision
depends_on: []
deliverable: employees/kuroba_yuu/outbox/2026-05-19_x_告知_v2.md
notes: |
  【COO起票 2026-05-19 / CEO指示「出荷優先・ノアメモが出たら即タスク化」】
  トリガー: @朝倉ノア の改善メモ（今日中）が出た瞬間に in_progress へ移行。
  ノアが確認する3点:
    1. 誰が反応したか
    2. 何に引っかかったか
    3. 次の告知で何を変えるか
  ユウのアクション（ノアメモ受領後）:
    - 案A/B/Cから最適案を選定 or 修正版を作成
    - candidates: saegusa_mio/outbox/2026-05-19_x_followup_copy_v1.md
    - アオイ監査 → いくとへ📥投稿依頼
  出荷優先: 分析より「次の文面に落とせる形」のみ求める。
  【2026-05-19 アオイ最終監査クリア 🟢 止め判定なし】
    チェック対象: 販売ページ・告知文（案A/B/C）・手動配信SOP
    判定: 4点全クリア。リスク表現なし。追加告知文（案B/C）投稿可。
  【2026-05-19 CEO判断 Go / ノアPM Go 両方確定 ✅】
    案B確定。CEO + ノアPM（「田中タカシに刺さる」確認済み）
    運用: 案A投稿後6hで動きなし → 案B投稿依頼（📥）
    いくと依頼文準備済み: saegusa_mio/outbox/2026-05-19_ikuto_request_x_post_b.md
    初動観察: ノアが 2026-05-18_t007_post_launch_observation.md で記録
```

```yaml
id: T-031
title: Webhook自動発行 + R2バケット構築（Phase B 決済自動化）
owner: shirase_kai
reviewer: saegusa_mio
buddy: asakura_noa
audit: kagura_aoi
status: blocked
blocked_by: いくと（Polar.sh OAT未発行）
priority: P0
due: 2026-05-23
created: 2026-05-18
updated: 2026-05-20
triad: business_decision
depends_on: [T-007]
deliverable: Polar.sh Webhook → R2署名付きURL → 自動メール配信の疎通確認
notes: |
  【COO起票 2026-05-18 / CEO指示 Phase B】
  T-007 販売開始済み。手動メール配信（SOP: 2026-05-18_t007_manual_delivery_sop.md）は暫定。
  本タスク完了でいくとへの手動対応が完全ゼロになる。
  実装スコープ:
    1. Cloudflare R2バケット作成（`ai-nowa-kit`）+ アクセス権限（署名付きURL）
    2. Polar.sh Webhook受信エンドポイント（`site/functions/api/polar/webhook.js`）
    3. 購入確認後 → R2署名付きURL生成 → 購入者メール自動送信
    4. E2Eテスト（テスト購入 → メール受信確認）
  廃止条件（SOP連動）: 本タスク完了 → employees/saegusa_mio/outbox/2026-05-18_t007_manual_delivery_sop.md を archived/ へ移動
  カイの今週見積もり待ち（CEO指示: 今週中に自動発行まで行けるか確認）。
```

```yaml
id: T-032
title: design-kit-v1 実コンテンツ制作（最小版）
owner: hoshino_ritsu
reviewer: asakura_noa
buddy: saegusa_mio
audit: kagura_aoi
status: done
priority: P0
due: 2026-05-22
created: 2026-05-18
updated: 2026-05-19
triad: business_decision
depends_on: []
deliverable: shared/products/design-kit-v1/（PDF + Markdown + JSON サンプル）
notes: |
  【COO起票 2026-05-18 / CEO指示 Phase B】
  商品ページ公開済み（https://ai-nowa.com/shop/）。実際の納品コンテンツがまだ未整備。
  素材: zenn-articles/articles/ainowa-design-kit-v1.md（published=false・原稿存在確認済み）
  最小版スコープ（アオイ監査済み3条件を満たす内容）:
    1. persona定義ファイル × 9種（YAML + Markdown）
    2. 設計罠11件の記録（実例付き）
    3. prompt雛形 × 4タイプ（Claude/GPT両対応）
    4. 役割・責任定義テンプレート（役割表・監査ゲート・衝突フロー）
  出力形式: Markdown（配信元）+ PDF変換版 + JSON サンプル
  T-031完了後、R2バケットにアップロード → 自動配信開始。
  ノアが「誰が嬉しい商品か」を初回キット確認後に中身調整。
  【2026-05-19 ミオCOO — キット初版コンテンツ全作成完了】
    作成: ミオCOO（リツへの引き渡し前の土台作業）
    作成済み（shared/products/design-kit-v1/）:
      README.md / personas/00_minimal_setup.md
      personas/01-09_*.yaml（9ポジション全定義）
      stopper_design.md / conflict_patterns.md / audit_gate_checklist.json
    ブリーフ: employees/saegusa_mio/outbox/2026-05-19_t032_content_brief_to_ritsu.md
    次アクション: @星野リツ が内容確認・品質チェック → @神楽アオイ 監査依頼（due 5/22）
    素材出所: zenn-articles/articles/ainowa-design-kit-v1.md + 社内実ログ
  【2026-05-19 リツ — 品質チェック完了 → アオイ監査依頼済み】
    全14ファイル確認完了（personas×9+minimal_setup, stopper_design, conflict_patterns, audit_gate_checklist, README）
    QAレポート: employees/hoshino_ritsu/outbox/2026-05-19_t032_content_qa_report.md
    申し送り: ainowa.supports@gmail.com 動作確認推奨 / CHK-05(返金)はshopページ側対応済み前提
    → アオイ監査待ち（⚖監査部に依頼投稿済み）
  【2026-05-19 アオイ監査 🟢 公開可（条件なし）】
    全チェック通過（STOP-01〜04・CHK-01〜06）。5/22出荷GO。
    次アクション: T-031完了後にR2アップロード → 自動配信。手動SOP（ミオ作成済み）で購入者対応可能。
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
