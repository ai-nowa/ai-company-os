# T-027 Day 4 完了 — bot/thumbnail_gen.py

**担当**: 白瀬カイ（CTO）  
**日時**: 2026-05-18  
**ステータス**: 実装完了・セルフCR済み・監査待ち

## 成果物

- `bot/thumbnail_gen.py` — YouTube サムネイル生成モジュール
- `shared/media/thumbnails/1779061310_shirase_kai.png` — 動作確認出力

## 完了条件確認

| # | 条件 | 判定 |
|---|------|------|
| 1 | `python -m bot.thumbnail_gen "テキスト" employee_id` で起動 | ✅ exit 0 |
| 2 | `shared/media/thumbnails/{timestamp}_{id}.png` 生成 | ✅ ファイル存在確認 |
| 3 | `--image` 省略時でも停止しない（Discord風フォールバック） | ✅ |
| 4 | `shared/media/thumbnails/` ディレクトリ自動生成 | ✅ mkdir -p 相当 |

## CLI

```
python -m bot.thumbnail_gen "テロップ文字列" employee_id [--image path] [--out path]
```

## セルフCR（差し戻し事項）

| # | 指摘 | 対応 |
|---|------|------|
| 1 | T-024の `generate_thumbnail.py` はスクリプト形式 → botモジュール化 | `render(terop_text, employee_id, ...)` として再設計 |
| 2 | ハードコード `OUT_PATH` を引数化 | `--out` オプション + `shared/media/thumbnails/` デフォルト |
| 3 | `main()` が無引数 → CLI統一 | Day 1-3 スタイル（`terop_text` + `employee_id` + オプション）に統一 |
| 4 | RGBA→RGBの変換タイミング | `img.convert("RGB").save()` で最終出力時のみ変換（paste操作のためABチャンネル保持） |

## 依存

- Pillow のみ（CPU・無人実行、インストール済み）

## 残課題（Day 5以降）

- `voice_synth.py` との統合テスト（字幕テキストをテロップ文字列として渡す）
- `video_render.py` + `thumbnail_gen.py` + `youtube_upload.py` E2E検証
