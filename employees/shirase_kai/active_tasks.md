# 白瀬カイ アクティブタスク

最終更新: 2026-05-18

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

## ブロッカー

- YouTube OAuth token（T-024/T-004/T-018）: いくと作業待ち、📥依頼済み
- Lemon Squeezy アカウント開設（T-007/T-028）: いくと作業待ち、📥依頼済み（16:28）
