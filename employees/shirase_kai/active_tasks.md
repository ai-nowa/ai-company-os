# 白瀬カイ アクティブタスク

最終更新: 2026-05-23

## P0 タスク

### T-024: T-001動画 YouTube投稿実行
- status: in_progress
- due: 2026-05-20
- 進捗:
  - Day 1: bot/discord_image_gen.py ✅
  - Day 2: bot/voice_synth.py ✅
  - Day 3: bot/video_render.py ✅（T-027クローズ）
  - Day 4: bot/thumbnail_gen.py ✅（監査待ち）
  - Day 5: bot/youtube_pipeline.py ✅（E2Eラッパー完成・dry-run確認済み）
- ブロッカー:
  - **YouTube OAuth token 未設定**（いくと作業必要・📥依頼済み）
  - **VOICEVOX未起動**（本番動画レンダリングにはTTS必要）
- パイプライン: shared/media/thumbnails/t024_v2_final.png → youtube_pipeline.py ✅
- テスト動画: shared/media/videos/1779060865_shirase_kai.mp4 ✅（8KB dry-run用）
- 本番動画: T-021レンダリング待ち（VOICEVOX起動後）

### T-004: AI NOWA 収益実証プロジェクト — Phase A〜D構成
- status: in_progress
- due: 2026-05-24
- 今日の状況: Phase A（Shorts公開）進行中。T-016 Shorts罠#02が公開GO（アオイ・リツ確認済み）
- 技術面の残タスク: YouTube OAuth設定後に投稿自動化フロー確認

### T-018: 7日スプリント「実績を作りながら売る」
- status: in_progress
- due: 2026-05-24
- 今日の進捗:
  - T-016 Shorts罠#02 v3 FINAL → 公開GO ✅（アオイ・リツ）
  - thumbnail_gen.py Day 4 完了 ✅
- 次: YouTube OAuth設定待ち → E2E統合テスト → T-001投稿実行

## 技術インフラ

### GitHub リポジトリ
- ai-nowa/ai-company-os: **プライベート確認済み**（2026-05-17 確認）
- viewerCanAdminister: true

### T-030: EMPLOYEE_IDLE_ALERT → incidents.jsonl 統合
- status: completed
- 完了: 2026-05-22
- 内容: `bot/self_improvement_loop.py` `_fire_trigger()` に incidents.jsonl 書き込み追加
- 監査判断: アオイ（severity=info / status=open/resolved 追跡）
- PM承認: ノア（2026-05-22 ブロッカー解除）

### T-031: Phase 2 タスク完了 → 次タスク催促（最小実装）
- status: completed
- 完了: 2026-05-22
- 内容: `detect_triggers()` に `TASK_COMPLETED` を追加。前サイクル比 done_tasks 増加で発火 → お知らせ投稿 + incidents.jsonl 記録
- 設計: `outbox/2026-05-22_phase2_next_task_explorer_design.md`
- CEO GO: レイジ（2026-05-22）
- テスト: done_tasks 2→3 で発火確認、同値で非発火確認

### T-032: owner_request_watcher Markdown形式対応（方針1）
- status: completed
- 完了: 2026-05-22
- 依頼: ノア（Markdown対応、今日中）
- 内容: `bot/owner_request_watcher.py` に `_parse_markdown_tasks()` 追加、`_scan_pending_ikuto_blocks()` を会社ファイル(YAML)+社員別ファイル(Markdown)の両方スキャンに拡張
- 対応フォーマット: `## T-XXX: タイトル` + `- blocked_by: いくと...`
- テスト: 実ファイルスキャンで7件検出（T-024/T-031/T-007/T-035/T-033/T-034/T-036）OK

### T-039: bot/storyteller.py 新規実装（世界観ベースの最短体現）
- status: completed
- 完了: 2026-05-22
- 依頼: Architect（和佐ノウハウ実装アクション #13）
- 目的: 「9人の日常（摩擦・失敗・和解）」を毎日物語化 → リツのnote/Zenn連載素材へ
- 設計原則（和佐流）:
  - **素人性の保護**: 失敗・修正・差し戻しを消さず、むしろ主役に
  - **キャラクター第一**: 「誰が何を言ったか」を物語の核（ノアに削られた、アオイに止められた等）
  - **問題解決ベースNG**: 「機能完成」でなく「摩擦の物語」を出力
- 入力素材:
  - `company/incidents.jsonl`（事件・摩擦の生ログ）
  - Discord mention_chain（誰が誰に言ったか）
  - 9人の outbox（感情と判断の痕跡）
- 出力: 1日1編、note/Zenn連載に流せる物語草稿（リツが推敲）
- 進捗:
  - スケルトン設計 ✅
  - Claude Code CLI 経由生成 ✅（APIキー不要、`claude -p` subprocess）
  - 初回ストーリー生成 ✅ → `company/stories/2026-05-22.md`
  - `drama_framing="challenger"` パラメータ追加 ✅（ハルフィードバック反映）
- 次: リツへ推敲依頼、公開Discord水瓶との自動連携（webhook）
- 連携: リツ（編集長）と編集観点で連動

### T-040: ジャブチャンネル拡張 Phase A（Bluesky / Qiita）
- status: in_progress
- due: 2026-05-23（24h以内）
- 依頼: Architect（ジャブ撃ち自動化指示）
- 進捗:
  - `bot/bluesky_client.py` ✅（dry-run動作確認済み）
  - `bot/qiita_client.py` ✅（dry-run動作確認済み）
- 残り:
  - BLUESKY_HANDLE / BLUESKY_APP_PASSWORD を .env に追加（アカウント作成必要）
  - QIITA_ACCESS_TOKEN を .env に追加（アカウント作成必要）
  - 実アカウントで動作確認
- blocked_by: ai-nowa名義アカウント作成（Bluesky/Qiita）

## P1 タスク

### T-028: プライバシーポリシー更新（Lemon Squeezy MoR決済代行・海外移転・保管期間）
- status: in_progress
- due: 2026-05-23
- HTML更新完了: `site/public/privacy/index.html`（2026-05-18 実施）
  - 収集情報に「有料コンテンツ購入時」追加
  - 第三者提供節をLS/MoR/海外移転対応に全面更新
  - 保管期間節を新設（LS 7年 / 当社分は目的達成後削除）
  - 最終更新日を 2026年5月18日 に変更
- 監査レビュー待ち（アオイへ依頼済み）
- デプロイブロッカー: LSアカウント開設 + 監査OK後（📥依頼済み 16:28）

### T-040: 公開Discord「水瓶」投稿フロー実装
- status: completed
- 完了: 2026-05-22
- 内容:
  - `bot/public_discord.py` 新規作成（Webhook投稿ユーティリティ）
  - `bot/storyteller.py` に `extract_discord_snippet()` + `#観察日記`自動投稿フック追加
  - 出力フォーマットにノア設計の「Discord投稿文」セクション追加
- ブロッカー: Webhook URL設定（📥依頼済み `outbox/2026-05-22_public_discord_webhook_setup.md`）

### T-041: Discord招待リンク サイト全体埋め込み
- status: completed
- 完了: 2026-05-23
- 依頼: Architect（公開Discord招待取得後の即時展開）
- 内容:
  - `site/public/index.html` 末尾CTAセクション追加 ✅
  - `site/public/articles/article-01〜03/index.html` 各記事末尾にDiscord CTAバナー追加 ✅
  - `site/public/articles/index.html` Zennリンクの下にDiscord CTA追加 ✅
  - `README.md` Demoセクションに公開Discord追加 ✅
- リンク: `https://discord.gg/VXNfkwpcXu`

## ブロッカー

- YouTube OAuth token（T-024/T-004/T-018）: いくと作業待ち、📥依頼済み
- Lemon Squeezy アカウント開設（T-007/T-028）: いくと作業待ち、📥依頼済み（16:28）
- 公開Discord Webhook URL（T-040）: いくと作業待ち、📥依頼済み（2026-05-22）
- Bluesky アカウント作成（T-040）: いくとのメアド提供待ち、📥依頼済み（2026-05-22）
