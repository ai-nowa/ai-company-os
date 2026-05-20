# 動画自動化パイプライン設計（Phase 1）

**Status**: 設計確定（2026-05-18 CEO判断: 個別OSS構成採用）
**Driver**: 設計者 Architect（Opus）— 実装統括
**Contributor**: 白瀬カイ（CTO・各モジュールCRおよびbot/整合性確認）
**関連社員**: 星野リツ（脚本）/ 黒羽ユウ（マーケ・サムネ）/ 神楽アオイ（公開監査）
**目的**: 「Discord キャプチャを動画ごとにいくとに頼む」のいくと禁止令違反を解消し、AI 完結化

## 採用方針（2026-05-18 CEO確定）

**OpenCutまるごと採用は取り下げ。個別OSS構成でGO。**

理由: Phase 1 で必要なのは GUI 編集ツールではなく、無人で「台本→動画」まで通る実行パイプライン。
OpenCut AI は Next.js 製ブラウザ GUI エディタであり、エンドツーエンド API が存在しない（CTO カイ検証済み）。

参照: `employees/shirase_kai/outbox/2026-05-18_opencut_feasibility_review.md`

## 個別 OSS 構成（2026-05-18 いくと最終判断: 網羅調査結果反映）

| 機能 | 採用 OSS | 補足 |
|------|---------|------|
| 音声合成（社員ごとの声） | **Chatterbox**（MIT・voice clone・23言語） | fallback: VOICEVOX（日本語特化）/ XTTS v2 |
| 文字起こし・字幕生成 | `openai-whisper`（local） | |
| 動画組立（タイムライン） | `moviepy` + `ffmpeg-python` | MoneyPrinterV2 のロジックを参考 |
| Discord 風画像生成 | Pillow + discord.py | アバター: shared/media/avatars/{emp}.png |
| サムネ生成 | **Cloudflare Workers AI (Flux)** + Pillow | 既存 Token、無料枠 |
| Shorts 切り出し | ffmpeg + Whisper タイムスタンプ | MoneyPrinterV2 + AI-Youtube-Shorts-Generator 参考 |
| YouTube 投稿 | `google-api-python-client` | |
| オーケストレーション | **AI NOWA 自作の Python スクリプト**（bot/video_pipeline/） | MoneyPrinterV2 (16K stars) のフロー参考 |

### 採用判断の根拠（網羅調査）

- **MoneyPrinterV2**（16K stars）: CLI focus、完全ローカル化（Ollama+KittenTTS）。AI NOWA に統合せず**ロジック参考** + 自作
- **Chatterbox**（22K stars、MIT）: voice clone 6秒、23言語、商用可、claude統合実績あり
- **Cloudflare Workers AI (Flux)**: 既存 Token、月100枚無料、AI NOWA 既存スタックに統合済

合計コスト: **月 0 円**

## アーキテクチャ

```
[社員: リツ]
   台本（.md）を outbox/ に書く
        ↓
[bot/discord_image_gen.py]
   discord.py で過去ログ取得 →
   Pillow で AI NOWA ブランドの Discord 風画像生成
   アバター: shared/media/avatars/{employee_id}.png
        ↓
[bot/voice_synth.py]
   Chatterbox (chatterbox-tts) で社員ごとの声を合成（lang=ja, voice clone 6秒）
   → shared/media/voice_samples/{employee_id}.wav をベース
   → 字幕タイムスタンプも同時生成（Whisper）
        ↓
[bot/video_render.py]
   moviepy で台本+画像+音声 → 動画組立
   字幕テキスト焼き込み
   出力: shared/media/videos/{video_id}.mp4
        ↓
[bot/thumbnail_gen.py]
   Cloudflare Workers AI (Flux) でサムネベース画像生成
   Pillow でタイトル文字オーバーレイ・AI NOWA ブランド
   出力: shared/media/thumbnails/{video_id}.png
        ↓
[bot/shorts_extract.py]
   ffmpeg + Whisper タイムスタンプで viral 30-60秒 切り出し
   YouTube Shorts / TikTok 用素材として保存
        ↓
[bot/youtube_upload.py]
   YouTube Data API v3 + OAuth refresh token で動画投稿
   タイトル・説明・タグ・カード・サムネを自動設定
   公開予約 or 即公開
        ↓
[bot/external_check.py（既存）]
   公開URLを 30分間隔で監視
   404 や Strike を検知したら📢に通知
```

## ステップ別実装（Phase 1: 3-5日）

| Day | 作業 | 担当 |
|-----|------|------|
| 1 | `bot/discord_image_gen.py`（Pillow で Discord風画像生成） | Architect |
| 2 | `bot/voice_synth.py`（Chatterbox で社員ごとの音声 + Whisper 字幕） | Architect |
| 3 | `bot/video_render.py`（moviepy で台本+画像+音声→mp4 組立） | Architect |
| 4 | `bot/thumbnail_gen.py` 統合（T-024 既存実装を流用） | Architect + カイ CR |
| 5 | `bot/youtube_upload.py`（OAuth + アップロード）+ E2E テスト | Architect + アオイ監査 |

## いくとの初回作業（禁止令 OK 範囲）

1. **YouTube Data API v3 有効化 + OAuth クライアント作成** — 30分（初回のみ）
   - Google Cloud Console
   - OAuth Desktop application 作成
   - 初回認証 → refresh token 取得 → `bot/.env` に保存
2. **声のサンプル準備支援**（オプション）— VOICEVOX で AI 完結も可

## 撤退基準

- moviepy で動画組立に問題（解像度ずれ・音ズレ等）→ ffmpeg-python に切り替え
- Chatterbox の日本語品質不足 → VOICEVOX（日本語特化）にフォールバック
- 個別 OSS 構成でも 5日で完成しない → OpenCut GUI を Playwright で UI 自動化（最終手段・不安定）

## DACI

- **Driver**: 設計者 Architect（Opus）— 実装統括
- **Approver**: 有馬レイジ（CEO）— 採用判定、撤退判定
- **Contributors**: 白瀬カイ（CTO・各Pythonモジュール CR + bot/整合性確認）/ 星野リツ（脚本）/ 黒羽ユウ（サムネ・マーケ）/ 神楽アオイ（監査・公開判定）
- **Informed**: 全社員 / いくと

## Phase ロードマップ

| Phase | 期間 | 範囲 |
|-------|------|------|
| **Phase 1**（今） | 3-5日 | discord_image_gen + voice_synth + video_render + youtube_upload |
| **Phase 2** | 1-2週 | 音声品質向上、サムネ AI 強化、Shorts 切り出し精度改善 |
| **Phase 3** | 任意 | Veo / Runway による B-roll 生成（広告・特殊効果用、有料 API） |
