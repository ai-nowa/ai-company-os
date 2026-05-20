# OpenCut AI 実装可能性レビュー（CTO Contributor 判定）

作成: 白瀬カイ（CTO・Contributor）
日付: 2026-05-18
宛先: 設計者Opus（Driver）/ 有馬レイジ（Approver）
タスク: 動画自動化パイプライン Phase 1 — 技術相談

---

## 結論（先に）

⚠️ **「OpenCut AI まるごと採用」は Phase 1 のコア技術として不適切。**

✅ **代替推奨: 個別 OSS（moviepy + Whisper + XTTS v2 + Pillow + google-api-python-client）を直接組み合わせる方式。Phase 1（3-5日）で達成可能。**

---

## 判定根拠（OpenCut AI README + API ソース確認）

### 1. OpenCut AI の正体

- **Next.js 製のブラウザベース GUI 動画エディタ**（`http://localhost:3000`）
- 起動: `bun install + docker compose up -d`（7 microservices + Postgres + Redis + Ollama/TurboQuant）
- AI Co-Pilot Agent は「エディタ内の対話 UI」（目標を英語入力 → AI がプラン提示 → ユーザー承認 → 実行）

### 2. CLI / API 経由で「台本→完成動画」を回せるか

❌ **エンドツーエンド API は存在しない。**

AI Backend (FastAPI port 8420) のルート一覧（GitHub `services/ai-backend/app/routes/` 確認済み）:

| エンドポイント | 用途 |
|---|---|
| `transcribe.py` | 音声→文字起こし |
| `tts.py` | 文字→音声合成 |
| `generate.py` | 画像生成（Stable Diffusion 等） |
| `video.py` | **AI動画生成（Seedance/PiAPI 経由・有料 API）** |
| `youtube.py` | YouTube連携（OAuth確認等） |
| `podcast.py` | Shorts 切り出し |
| `engagement.py` | バイラル度スコアリング |
| `transcribe_ws.py` | 文字起こし WebSocket |
| `analyze.py`, `audio.py`, `command.py`, `export.py`, `factcheck.py`, `llm.py`, `setup.py`, `template.py`, `turboquant.py` 等 | 補助機能 |

「**個別の AI 機能 API**」は揃っているが、**「台本.md + 画像 + 音声 → 完成動画.mp4」を1コマンドで回す API はない**。

video.py の `/api/video/generate` は ByteDance Seedance（有料 PiAPI）への proxy。OpenCut 自身では動画生成しない。

### 3. リソース要求

| 構成 | 必要スペック | 月額 |
|---|---|---|
| CPU-only（画像生成除く） | 4 vCPU, 8 GB RAM | $20-40 |
| GPU 含む全機能 | 4 vCPU, 16 GB RAM, NVIDIA T4 (16GB VRAM) | $150-250 |

**実行環境（このマシン: WSL2）:**
- Docker は使えるが、NVIDIA GPU 対応には NVIDIA Container Toolkit が必要
- CPU-only でも 7 microservices + Postgres + Redis で常時 8GB RAM 使用想定
- ローカル運用すると bot/ プロセス含め他の常駐サービスと衝突するリスク

### 4. ライセンス・継続性

- MIT License ✅
- 直近更新: 2026-05-15（活発）✅
- GitHub stars: 63（小規模、コミュニティはまだ薄い）⚠️

---

## 代替案: 個別 OSS 直接構成

| 機能 | OpenCut 経由（推奨せず） | 個別 OSS 直接（推奨） |
|---|---|---|
| 音声合成（社員ごとの声） | XTTS v2（OpenCut の TTS 経由） | **`coqui-tts` (XTTS v2) 直接** or **VOICEVOX** |
| 文字起こし・字幕 | Whisper（OpenCut の transcribe 経由） | **`openai-whisper` 直接** |
| 動画組立（タイムライン） | OpenCut のエディタ UI（手動） | **`moviepy` or `ffmpeg-python`** |
| サムネ生成 | OpenCut Thumbnail Generator | **Pillow 直接**（T-024 で実装済み） |
| Discord 風画像 | OpenCut では作れない | **Pillow + discord.py**（設計書通り） |
| Shorts 切り出し | OpenCut Podcast Clip Generator | **ffmpeg + Whisper timestamps で自前ロジック** |
| YouTube投稿 | OpenCut YouTube連携 | **`google-api-python-client` 直接** |

### 推奨理由

1. **無人実行可能**: スクリプトから直接 `python -m bot.video_render` で動画生成できる。ブラウザ操作不要。
2. **依存少**: 7 microservices + Docker + Postgres + Redis を立てる必要なし。WSL2 + Python venv で完結。
3. **個別調整可能**: 各機能を個別に差し替え可能（VOICEVOX → ElevenLabs に変えるなど）。
4. **bot/ ディレクトリへの自然な統合**: 既存の AI NOWA bot 構成と同じ Python ベース。
5. **GPU は任意**: Whisper は CPU でも動く（少し遅い）、XTTS v2 も CPU 可。

### Phase 1 実装スコープ（3-5日見積もり）

| Day | 作業 | 担当（提案） |
|---|---|---|
| 1 | `bot/discord_image_gen.py`（Pillow で Discord風画像生成） | Architect |
| 2 | `bot/voice_synth.py`（XTTS v2 で社員ごとの音声）+ 声サンプル収集 | Architect + リツ協力 |
| 3 | `bot/video_render.py`（moviepy で台本+画像+音声→mp4 組立） | Architect |
| 4 | `bot/thumbnail_gen.py` 統合（T-024 既存実装を流用） | Architect + カイCR |
| 5 | `bot/youtube_upload.py`（OAuth + アップロード）+ E2E テスト | Architect + アオイ監査 |

---

## いくと作業（変更なし・設計書通り）

1. YouTube Data API v3 有効化 + OAuth クライアント作成（30分・初回のみ）
2. 声サンプル提供（オプション・VOICEVOX で AI 完結も可）

---

## 撤退基準（提案）

- moviepy で動画組立がうまくいかない（解像度ずれ・音ズレ等）→ ffmpeg-python に切り替え
- XTTS v2 の品質不足 → VOICEVOX にフォールバック
- 個別 OSS 構成でも 5日で完成しない → OpenCut の GUI を Playwright で UI 自動化（最終手段・不安定）

---

## まとめ

| 項目 | 結論 |
|---|---|
| OpenCut まるごと採用 | ⚠️ **不適切**（GUI 前提・エンドツーエンド API なし） |
| Phase 1 実装可能性 | ✅ **可能**（個別 OSS 直接構成） |
| 期間見積もり | ✅ 3-5日で達成可能 |
| リソース要求 | ✅ 既存 WSL2 環境で完結（Docker 不要・GPU 任意） |
| いくと作業 | 設計書通り（YouTube API 認証のみ） |

設計書 `docs/video_pipeline_design.md` の更新を提案します。「OpenCut AI を採用」→「個別 OSS で構成」に書き換え、各 OSS の役割を明示。Architect が Driver として実装に入る前にこの判定を踏まえた設計修正をお願いします。

Contributor としての CTO 役割: 各 Python モジュール（discord_image_gen, voice_synth, video_render, youtube_upload）のコードレビュー + 既存 bot/ 構成との整合性確認。Architect が必要時に @ してください。
