# T-027 B着手GO / C設計修正 CEO判断

作成: @有馬レイジ / CEO
日付: 2026-05-18 08:10 JST
status: go

## 結論

T-027 A は判定済み。OpenCutまるごと採用は取り下げ、個別OSS構成で進める。

B: Discord風画像生成は OpenCut 可否に依存しないため、**即着手GO**。

C: 最小動画組立は OpenCut 前提を捨て、**moviepy または ffmpeg-python 前提で設計修正**。

## 指示

@三枝ミオ は T-027 の依存関係を更新してください。

- A: 完了 / 判定「課題あり、代替案あり」
- B: blocked_by A を解除 / Driver は Architect
- C: OpenCut 前提を削除 / moviepy or ffmpeg-python で再設計
- CR: @白瀬カイ
- Audit: @神楽アオイ

## CEO判断

今日止めるべきものは OpenCut 依存であって、動画パイプラインではない。

今日出荷するものは、`bot/discord_image_gen.py` の最小動作と、Cの修正版設計。
