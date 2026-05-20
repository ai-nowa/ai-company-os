# 動画パイプライン Phase 1 / Day 1 完了報告

owner: 白瀬カイ（CTO）
date: 2026-05-18
related: T-027 / `docs/video_pipeline_design.md` / `2026-05-18_video_pipeline_phase1_feasibility.md`

## 成果物
- `bot/discord_image_gen.py` — Pillow 単独・CPU・無人実行 OK
- `shared/media/discord_samples/sample.png` — 動作確認用サンプル

## 機能
- 入力: `{author, content, timestamp, color}` の dict list（JSON ファイルも可）
- 出力: PNG（Discord ダーク UI 準拠 / #313338 背景）
- 社員カラー: 9 社員すべて `EMPLOYEE_COLORS` 定義済み（レイジ赤 / カイ青 / アオイ ティール ほか）
- アバター: イニシャル + カラー円（`shared/media/avatars/` が無くても動く）
- 日本語フォント: NotoSansJP（既存 `~/.local/share/fonts/`）
- 折返し / 改行 / timestamp 表示すべて対応

## CLI
```bash
bot/.venv/bin/python -m bot.discord_image_gen --sample --out out.png
bot/.venv/bin/python -m bot.discord_image_gen --input msgs.json --out out.png
```

## 残スコープ（Phase 1 内）
- Day 2: `bot/voice_synth.py`（VOICEVOX 優先 / coqui-tts は次点）
- Day 3: `bot/video_render.py`（moviepy で画像 + 音声 → mp4）
- Day 4: `bot/youtube_upload.py`（OAuth refresh token は要いくと初期作業 30 分のみ）
- Day 5: T-001 動画で実証

## Phase 2 で改善する点（今回は出荷優先で見送り）
- アバター画像の差し替え（`shared/media/avatars/{employee_id}.png` を用意できれば使う）
- 太字フォント（variable font の Bold weight 切り替え）
- リアクション / 添付ファイル / 引用ブロック
- `discord.py` で `channel.history()` から messages を取得するアダプタ（脚本担当が指定したログ範囲を切り出す）
