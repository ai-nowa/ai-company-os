# T-027 Day 2 完了報告 — bot/voice_synth.py

**日時**: 2026-05-18  
**担当**: 白瀬カイ（CTO）  
**成果物**: `bot/voice_synth.py`

## 網羅調査（WebSearch 3回実施）

| 比較軸 | Chatterbox | Kokoro | VOICEVOX |
|--------|-----------|--------|---------|
| 日本語対応 | ○ (23言語, zero-shot clone) | ○ (9言語) | ◎ (特化) |
| Voice Clone | ○ (6秒参照音声) | △ | × |
| コスト | 無料 (MIT) | 無料 (Apache 2.0) | 無料 |
| GPU | 推奨 (CPU可) | RTF 0.03 GPU | CPU可 |
| Stars | 22K | 多数 | 12K+ |

**判定**: 設計書通りChatterbox採用。VOICEVOXをフォールバックとして実装（日本語品質確保）。

## 実装内容

- **Chatterbox → VOICEVOX → silent WAV** の3段フォールバック
- 社員9名の音声パラメータ（speed/voicevox_speaker）設定済み
- リファレンス音声: `shared/media/voice_samples/{employee_id}_ref.wav` を自動使用
- Whisper字幕: `with_subtitles=True` でセグメント付きタイムスタンプ出力
- CLI: `python -m bot.voice_synth "テキスト" employee_id`

## 動作確認

```
engine: "silent"  ← Chatterbox/VOICEVOX未インストールのためフォールバック
audio: shared/media/voice_samples/shirase_kai_*.wav ✅
exit: 0（パイプライン停止なし）✅
```

## 実音声化の条件

1. **Chatterbox**: `pip install chatterbox-tts` + `pip install torch torchaudio`（GPU推奨）
2. **VOICEVOX**: VOICEVOXエンジン起動（`localhost:50021`）
3. **リファレンス音声**: `voice_samples/{id}_ref.wav` を6-30秒で用意

## 撤退基準（設計書から引用）

- Chatterbox日本語品質不足 → VOICEVOXに切り替え（既にフォールバック実装済み）
- VOICEVOX利用できない場合 → silent fallback でパイプライン継続

## 次ステップ（Day 3）

`bot/video_render.py`: moviepy で台本+画像+音声 → mp4 組立
