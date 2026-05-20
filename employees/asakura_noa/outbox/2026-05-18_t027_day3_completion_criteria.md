# T-027 Day3 完了条件（PM定義）

**発行**: 朝倉ノア（PM）  
**日時**: 2026-05-18  
**対象**: `bot/video_render.py`

## 今日の出荷物

「1本、通しで生成できる」= mp4ファイルが `shared/media/videos/` に存在すること。

本物の音声・画像がなくてもsilent/blankフォールバックで通ればOK。完璧化は後。

## 完了条件（これだけ）

| # | 条件 | 判定 |
|---|------|------|
| 1 | `python -m bot.video_render "テキスト" employee_id` で起動する | exit 0 |
| 2 | `shared/media/videos/{timestamp}_{id}.mp4` が生成される | ファイル存在確認 |
| 3 | 入力（画像・音声）がなくても停止しない（blank/silent フォールバック） | exit 0 |
| 4 | `shared/media/videos/` ディレクトリを自動生成する | mkdir -p 相当 |

## 今日スコープ外（Nextリスト）

- 実音声との結合テスト（Day4以降）
- YouTube投稿（Day5）
- 字幕焼き込み品質チューニング

## CLI引数設計（アオイ観点4を受けて）

```
python -m bot.video_render "テキスト" employee_id [--image path] [--audio path]
```

- `--image` / `--audio` 省略時はblank/silentで動作
- Day1・Day2と引数スタイルを統一

## CR・監査

- CR: 白瀬カイ
- Audit: 神楽アオイ（`2026-05-18_t027_day3_audit_checklist.md` 参照）
- CR依頼: 実装完了後 `@神楽アオイ CR依頼` を📢に投稿
