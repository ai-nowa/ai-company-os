# ビジネス指標監視 — 緊急計画書
作成: 2026-05-18 ユウ（Architect介入受け）

## 問題認識
マーケターである私が「会社の事業成績」を監視していなかった。完全な失態。
T-004/T-018 の撤退基準は数字なしでは機能しない。

## 現状の空白

| チャネル | 現状 | 何が見えていない |
|----------|------|-----------------|
| ai-nowa.com | GA なし | PV/UU/流入元 |
| YouTube | Analytics API 未呼び出し | 再生数/登録者 |
| Zenn | URL 死活のみ（かつ 404！） | article view 数 |
| Lemon Squeezy | 未接続 | 売上/購入数 |

## 今日中に実行できること（いくと不要）

### 1. Zenn ビュー数スクレイプ（即実装可）
- `https://zenn.dev/ai_nowa/articles/{slug}` の `<meta name="description">` or OGP でビュー数取得
- `external_check.py` の拡張として `zenn_metrics.py` に分ける
- watched_urls.json の URL も修正（現在 zenn.dev/yikuto/... が 404）

### 2. YouTube Analytics API（OAuth 既設）
- `bot/youtube_oauth_setup.py` の OAuth トークンで `youtubeAnalytics.v2` を呼ぶ
- スコープ: `https://www.googleapis.com/auth/yt-analytics.readonly`
- 取得: 再生数・ユニーク視聴者・チャンネル登録者数
- 日次で `company/metrics_snapshot.jsonl` に記録

### 3. Lemon Squeezy API
- `/v1/orders` エンドポイント（APIキー: env `LEMONSQUEEZY_API_KEY`）
- 日次売上・購入件数を snapshot に追記

## いくと依頼が必要なもの

### GA タグ埋め込み（Cloudflare Pages デプロイ）
- `site/public/index.html` に `gtag.js` 追加
- GA4 プロパティ作成 or 既設 ID の共有
- デプロイは私が実行できるが、GA アカウントがいくと管理

## 実装優先順位

1. **今日**: Zenn URL 修正 + ビュー数ポーリング実装
2. **明日**: YouTube Analytics 日次取得スクリプト
3. **今週**: Lemon Squeezy 売上追跡
4. **いくと確認後**: GA タグ埋め込み

## タスク提案

新規タスク: `T-026` — ビジネス指標監視システム構築（P0, 担当: ユウ）
- T-004/T-018 の撤退基準「数字が取れること」の前提条件

## dashboard.md への追加案

```
## 事業指標（日次）
| 指標 | 直近値 | 前日比 |
|------|--------|--------|
| Zenn記事PV（合計） | - | - |
| YouTube 再生数（累計）| - | - |
| YouTube 登録者数 | - | - |
| LS 売上（当月）| - | - |
```
