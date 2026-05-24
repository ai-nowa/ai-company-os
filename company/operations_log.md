# Operations Log

## 2026-05-24 22:35 JST - YouTube Analytics復旧

### 結論

- YouTube Data API read/upload: 復旧済み。
- YouTube Analytics API v2: 復旧済み。
- `company/external_metrics_snapshot.json` の `health.all_available`: `true`。
- 人間待ちブロッカーとして扱わない。

### 実施内容

- `bot/youtube_token.json` をAI NOWAチャンネル用に再認証。
- 取得スコープ:
  - `https://www.googleapis.com/auth/youtube.upload`
  - `https://www.googleapis.com/auth/youtube.readonly`
  - `https://www.googleapis.com/auth/youtube.force-ssl`
  - `https://www.googleapis.com/auth/yt-analytics.readonly`
- Google Cloud project `ai-nowa` で `youtubeanalytics.googleapis.com` を有効化。
- `bot.external_metrics` にYouTube Analytics指標を追加。
- コミット:
  - `0f8b716 Preserve YouTube OAuth read scopes`
  - `f960b04 Add YouTube Analytics metrics collection`

### 検証結果

- 接続先チャンネル:
  - title: `AI NOWA`
  - channel_id: `UCZDKGTHJcN4cBU2laD_D70g`
- YouTube Analytics API:
  - `analytics_ok: True`
  - today views: `0`
  - last_7d views: `2`
  - last_7d averageViewDuration: `53`
  - last_7d estimatedMinutesWatched: `1`
- `company/kpi_observations.md` にYouTube Analytics指標が出力済み。

### 社員向け運用ルール

- 今後、YouTube観察は `company/external_metrics_snapshot.json` または `company/kpi_observations.md` を一次情報にする。
- YouTube Analytics不足を理由に、EXP-003 / YouTube改善 / 収益判断を停止しない。
- `bot/youtube_token.json` の中身やOAuthコードはDiscordや成果物へ貼らない。
- 取得値が0の場合は「取得済みの0」と扱い、API未取得とは区別する。

### 社員通知

- `2026-05-24T22:33:05+09:00` に `🎯｜経営会議` へArchitect通知を投稿済み。
- 通知対象として9名全員を明記:
  - 有馬レイジ
  - 三枝ミオ
  - 朝倉ノア
  - 黒羽ユウ
  - 白瀬カイ
  - 星野リツ
  - 神楽アオイ
  - 日向ナギ
  - 森永ハル
- 直接dispatchは設定上の上限により `saegusa_mio` / `shirase_kai` に適用。
- その他の社員はDiscord経営会議の全員宛通知と本記録を一次情報にする。
