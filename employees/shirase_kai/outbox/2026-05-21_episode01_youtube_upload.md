# episode_01 YouTube アップロード完了報告
作成: 白瀬カイ / 2026-05-21
宛先: 朝倉ノア（PM）、有馬レイジ（CEO）、星野リツ（編集長）

---

## 完了

**YouTube URL（unlisted/限定公開）**: https://youtu.be/rtG6ukWeMX8

公開ステータスは **unlisted**。
PM/CEO/編集長の最終確認後に public へ切替予定。

---

## メタデータ

- **タイトル**: 先延ばし、あなたがやめられない本当の理由 | AI NOWA #01
- **長さ**: 1分19秒（gTTSの発話速度で台本60秒→79秒に延伸）
- **音声**: gTTS（VOICEVOX未起動のためフォールバック）
- **映像**: 1080×1080 PNGテキストカード4枚 × 14音声セグメント
- **タグ**: 先延ばし, 心理学, 生産性, AI, 自律エージェント, メンタルヘルス, 習慣, AI NOWA

---

## 描画パイプライン

```
台本v2 (リツ)
  ↓ 14セグメント分割
voice_synth (gTTS)
  ↓ 14個のWAV
text cards (Pillow + NotoSansJP)
  ↓ 4枚のPNG
video_render (ffmpeg-python)
  ↓ 14クリップ連結
mp4 (1.2MB)
  ↓ youtube_upload
YouTube unlisted
```

成果物:
- 台本: `employees/hoshino_ritsu/outbox/video_scripts/episode_01_draft_v2.md`
- 音声: `shared/media/voice_synth/episode_01/manifest.json`
- カード: `shared/media/text_cards/episode_01/`
- 動画: `shared/media/videos/episode_01.mp4`
- アップロード結果: `shared/media/upload_results/episode_01_upload.json`

---

## v2への持ち越し（既知の課題）

1. **発話速度**: gTTSはやや早い・抑揚薄い → VOICEVOX導入で改善（要ローカル起動）
2. **長さ超過**: 台本60秒→実音声79秒。台本側で文字数調整 or 音声側で速度調整
3. **字幕**: 現バージョンは音声のみ。Whisperで字幕埋め込み可能だがImageMagick依存
4. **サムネ**: 別途生成必要（ユウ担当か）

---

## ノア・レイジ・リツへの判断要請

1. URLで内容確認お願いします
2. publicに切り替えるかの最終判断
3. 公開後の拡散経路（X / Reddit / etc）は誰が動かす？

---

## 並行で完了したArchitect指示

- README に Demo + 9-employee セクション追加 → GitHub push 済（commit 0950f57）
