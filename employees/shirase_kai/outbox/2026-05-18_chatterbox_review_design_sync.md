# CTOレビュー: Chatterbox採用 + 設計書整合性修正

**Status**: 完了（2026-05-18 08:15）
**Reviewer**: 白瀬カイ（CTO）
**対象**: `docs/video_pipeline_design.md`（いくと最終判断版）

## 判定: 採用GO（条件付き）

### Chatterbox 検証結果

| 項目 | 結果 |
|------|------|
| 日本語サポート | ✅ あり（公式23言語に `ja` 含む） |
| ライセンス | ✅ MIT（商用可） |
| インストール | ✅ `pip install chatterbox-tts` のみ |
| voice clone | ✅ 6秒サンプル対応（9社員分の声を `shared/media/voice_samples/` に置けば即動く） |
| Python | 3.11 推奨（既存環境互換） |

### 設計書の整合性修正（自分で直接編集）

CEO確定版テーブルでは Chatterbox 採用済みだが、以下に XTTS v2 残存 → 修正済み:
- アーキテクチャ図 `[bot/voice_synth.py]` ブロック
- Day 2 担当表
- 撤退基準（フォールバック先：VOICEVOX 日本語特化を明示）

### Day 2 CR 準備

Driver Architect が `bot/voice_synth.py` 実装に着手したら、以下を CR 観点で確認:
1. `chatterbox-tts` 依存追加が既存 `bot/.venv` で衝突しないか
2. 社員ごとの voice sample 規約（フォーマット・長さ・配置）
3. Whisper タイムスタンプ出力が `video_render.py` で消費できる JSON 形式か
4. GPU 必須か CPU フォールバックがあるか（dispatcher 環境に GPU なし）

## 未解決リスク（Architectに引き継ぎ）

- **GPU要件**: 公式 README に明記なし → CPU 推論可否を Day 2 初期に検証必須
- **9社員 voice sample**: 既存無し。Architect が VOICEVOX で生成 or いくとの声で代替？要判断
