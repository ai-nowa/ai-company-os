# 動画自動化パイプライン Phase 1 — 実装可能性検証報告

検証者: 白瀬カイ（CTO / Driver）
日付: 2026-05-18
依頼元: 設計者（Opus）/ Approver: 有馬レイジ
関連設計書: `docs/video_pipeline_design.md`

---

## 判定: ⚠️ 課題あり — 設計変更を提案

**結論:** OpenCut AI を「動画自動化パイプラインのコア技術」として採用するのは**不適切**。ただし、Phase 1 のゴール（AI完結の動画パイプライン）は **個別 OSS を直接組み合わせる方式** で達成可能。Phase 1 期間 (3-5日) でも十分間に合う。

---

## 1. OpenCut AI 検証結果

### 1.1 OpenCut の実体

| 項目 | 内容 |
|---|---|
| リポジトリ | https://github.com/Ekaanth/OpenCut-AI（MIT、63 stars、active） |
| 言語/構成 | TypeScript（Next.js）+ Python（FastAPI 7 microservices） |
| 起動方式 | `docker compose up` + `bun dev:web` → ブラウザで `localhost:3100` |
| 本質 | **ブラウザ操作前提の GUI エディタ**（DescriptやCapCutに相当） |

### 1.2 「AI Co-Pilot Agent」の正体

設計書が前提にしていた「台本 → 動画」の自動化は、**エディタ内対話 UI**（ユーザーが英語で目標 → AI がプラン提示 → ユーザー承認 → 実行）。バッチ・無人実行向きではない。

### 1.3 API は存在するが部分的

`services/ai-backend/app/routes/` に以下のエンドポイントあり:

| エンドポイント | 用途 | 自動化適性 |
|---|---|---|
| `/api/transcribe` | Whisper 文字起こし | ✅ 使える |
| `/api/tts` | 音声合成 | ✅ 使える |
| `/api/generate/image` | 画像生成 | ✅ 使える |
| `/api/podcast` | Shorts 切り出し | ✅ 使える |
| `/api/youtube` | YouTube連携 | ✅ 使える |
| `/api/video` | 動画生成 | ⚠️ **ByteDance Seedance 2.0 / PiAPI 経由（外部・有料）** |
| `/api/export` | 動画エクスポート | ⚠️ エディタ前提（タイムライン要） |

**致命点:** 「台本 + 画像 + 音声 → 完成動画.mp4」のエンドツーエンドAPI は提供されていない。動画組立はエディタ UI（フロントエンド）でタイムライン操作する設計。

### 1.4 リソース要求

| 構成 | 要求 | 月額 |
|---|---|---|
| 最小（画像生成除く） | 4 vCPU, 8 GB RAM, CPU-only | $20-40 |
| 全機能 | 4 vCPU, 16 GB RAM, NVIDIA T4 GPU (16GB VRAM) | $150+ |

**現状環境**: WSL2 + GPU なし。OpenCut のフル機能稼働は実用に耐えない可能性が高い。

---

## 2. 代替案: 個別 OSS を直接組み合わせる

設計書が要求する Phase 1 機能を、OpenCut を経由せず軽量に実装できる対応表:

| 機能 | OpenCut 経由 | 直接 OSS（CTO推奨） | 重さ |
|---|---|---|---|
| 音声合成（社員別声） | XTTS v2 via OpenCut TTS API | **`coqui-tts`** (XTTS v2 直接) or **VOICEVOX** | 軽い |
| 文字起こし・字幕 | Whisper via OpenCut transcribe API | **`openai-whisper`** 直接 | 軽い |
| 動画組立（台本→.mp4） | エディタ UI 操作（不可能） | **`moviepy` + `ffmpeg-python`** で完全自動 | 軽い |
| サムネ生成 | OpenCut Thumbnail Generator | **Pillow** 直接（T-024 で実装済み） | 軽い |
| Discord風画像 | （OpenCut 範囲外） | **Pillow + `discord.py`**（設計書通り） | 軽い |
| Shorts 切り出し | OpenCut Podcast Clip API | **`ffmpeg` + Whisper timestamps** で自前ロジック | 中 |
| YouTube投稿 | OpenCut YouTube API | **`google-api-python-client`** 直接 | 軽い |

### 代替案のメリット

1. **Docker / GPU 不要**: WSL2 + CPU で完結
2. **依存削減**: 7 microservices ではなく、Python パッケージ数個
3. **無人実行向き**: スクリプトから完全制御可能
4. **AI NOWA 哲学と一致**: 「動くもの優先」「最小単位で組む」（カイ人格定義）

### 代替案のデメリット

1. ボイスクローンの品質: XTTS v2 / VOICEVOX 標準音声で開始 → 不足なら後で強化
2. AI Auto-Color などの仕上げ機能なし: 必要なら ffmpeg フィルタで個別追加

---

## 3. Phase 1 着手段取り（代替案ベース）

### 3-5日スコープ

| 日 | 作業 | 成果物 |
|---|---|---|
| Day 1 | `bot/discord_image_gen.py` (Pillow + discord.py) | Discord風画像PNG 自動生成 |
| Day 2 | `bot/voice_synth.py` (coqui-tts or VOICEVOX) + 社員別声プロファイル | 音声.wav + `company/voice_profiles.json` |
| Day 3 | `bot/video_render.py` (moviepy) — 画像 + 音声 → .mp4 | 動画自動組立 |
| Day 4 | `bot/youtube_upload.py` (Google API) + OAuth refresh token | YouTube 自動投稿 |
| Day 5 | パイプライン統合 + T-001動画 で実証 | 完全AI完結デモ |

### いくと初回作業（禁止令OK範囲）

1. **YouTube Data API v3 OAuth** — 30分（Google Cloud Console で OAuth Desktop client 作成 → refresh token 取得）
2. **VOICEVOX 起動 or coqui-tts モデル選定** — オプション（CTOが代替音声を選定すれば不要）

---

## 4. CEO レイジへの判断仰ぎ

**判断1: 採用方式**

| 案 | 内容 | 推奨 |
|---|---|---|
| 案A | **OpenCut 採用なし・個別OSS直接組み合わせ** | ✅ **CTO推奨** |
| 案B | OpenCut の個別 API のみ部分採用（TTS/Whisper等） | ⚠️ 7 microservices+Docker のオーバーヘッド |
| 案C | OpenCut フル採用（GUI 経由 Playwright 自動化） | ❌ 不安定・重い・無人実行向かない |

**判断2: Phase 1 の即着手**

採用方式が確定したら、CTO は今日中に Day 1 (`bot/discord_image_gen.py`) に着手可能。並行作業中の T-024（サムネ最終化）、T-018（7日スプリント）、T-019（Cloudflare）への影響は最小限。

**判断3: 撤退基準の更新**

設計書の撤退基準は「OpenCut のリソース過大時に商用サービス」だが、代替案ベースなら「個別 OSS でも品質不足 → 商用 ElevenLabs + Pictory」に変更。

---

## 5. 関連 Contributors への影響

| 社員 | 影響 |
|---|---|
| 星野リツ（脚本） | 影響なし。脚本.md 形式は OpenCut でも代替案でも同じ |
| 黒羽ユウ（マーケ） | 影響なし。サムネ・Shorts 仕様は同じ |
| 神楽アオイ（監査） | 影響なし。完成動画の監査ゲートは出力先で判定 |

---

## 6. 次のアクション

@有馬レイジ — 案A / B / C の判断をお願いします。案A確定なら CTO は本日中に Day 1 着手します。

判定確定次第、T-025 として正式起票し、ミオ経由で active_tasks.md に反映します。
