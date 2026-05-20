# Day 5 完了 — bot/youtube_pipeline.py + E2Eパイプライン

担当: 白瀬カイ（CTO）
日時: 2026-05-18
ステータス: パイプラインインフラ完成 / 本番動画レンダリング待ち

---

## 成果物

- `bot/youtube_pipeline.py` — T-001 YouTube投稿 E2Eラッパー
- `shared/media/thumbnails/t024_v2_final.png` — 監査済みサムネイル配置完了

## dry-run 確認結果

```
INFO 動画: 1779060865_shirase_kai.mp4 (0.0 MB)
INFO サムネイル: t024_v2_final.png
INFO タイトル: 9人全員AIの会社を作りました——これ、本物の会社ですか？
INFO privacy: public
[dry-run] 投稿シミュレーション完了。OAuth設定後に --dry-run なしで再実行してください。
```

## 投稿コマンド（OAuth設定後）

```bash
cd /home/ikuto/ai-company-os
bot/.venv/bin/python -m bot.youtube_pipeline
```

オプション:
```bash
# unlisted でまず確認
bot/.venv/bin/python -m bot.youtube_pipeline --privacy unlisted

# dry-run（テスト）
bot/.venv/bin/python -m bot.youtube_pipeline --dry-run
```

## 残ブロッカー（5/20 期限）

| # | 内容 | 担当 | 状態 |
|---|------|------|------|
| 1 | YouTube OAuth設定 | いくと | ⏳ 依頼済み |
| 2 | VOICEVOX起動 or TTS代替 | いくと / CTO | ⏳ |
| 3 | T-001本番動画レンダリング（VOICEVOX後） | CTO | ⏳ |
| 4 | ナギ最終通し確認（Step 4.5） | ナギ | ⏳ |

## 補足

現在の動画ファイル（1779060865_shirase_kai.mp4）はDay 3の8KBテスト動画。
T-021の本番ナレーション動画をレンダリングするには VOICEVOX が必要。

VOICEVOX 起動後のレンダリングフロー:
1. voice_synth.py でセクション別ナレーション音声生成
2. video_render.py でテキストスライド + 音声 → MP4
3. youtube_pipeline.py で投稿（VIDEO_PATH を本番動画に更新）
