# X API 環境変数・権限・保存方法 1枚仕様書

作成: 白瀬カイ / CTO
日付: 2026-05-21
目的: いくとがX Developer Consoleで取得したキーを、迷わず安全にbotへ受け渡すための仕様
関連: `employees/arima_reiji/outbox/2026-05-21_x_api_key_blocker_ceo_decision.md`

---

## 1. いくとが取得する5つの値（X Developer Console）

| 名称 | 用途 | 環境変数名 |
|------|------|-----------|
| API Key (Consumer Key) | App識別子 | `X_API_KEY` |
| API Key Secret (Consumer Secret) | App認証 | `X_API_SECRET` |
| Access Token | アカウント認証 | `X_ACCESS_TOKEN` |
| Access Token Secret | アカウント認証 | `X_ACCESS_TOKEN_SECRET` |
| Bearer Token | v2 read系で使用 | `X_BEARER_TOKEN` |

## 2. 必要な権限スコープ

X Developer Portal > Project > App > User authentication settings:
- **App permissions**: `Read and Write`（投稿のため必須。`Read and write and Direct message` までは不要）
- **Type of App**: `Web App, Automated App or Bot`
- **Callback URI**: 不要（OAuth 1.0a User Context使用、botは事前にトークン取得済みで動作）

動画投稿対応時に追加で必要:
- v1.1 `media/upload` エンドポイントへのアクセス（standard accessで使えるはず、Free tierでも可能性あり）

## 3. 秘密情報の保存方法

**いくとへの渡し方（Discordに貼らない）**:
1. いくとはローカルマシン上でファイル `~/x_api_keys.txt` に値を書く（一時ファイル）
2. カイ（bot）が `bot/x_credentials_import.py` を1回実行（カイが用意するスクリプト）
3. 取り込み後、`bot/x_credentials.json` (chmod 0o600) に保存される
4. いくとは `~/x_api_keys.txt` を削除

**保存先・形式**（既存YouTube tokenと同じパターン）:
```
bot/x_credentials.json (chmod 0o600)
{
  "api_key": "...",
  "api_secret": "...",
  "access_token": "...",
  "access_token_secret": "...",
  "bearer_token": "..."
}
```

**読み込み**: `bot/config.py` に `load_x_credentials()` を追加（既存パターン踏襲）

## 4. dry-runで先に作るもの（APIキー不要）

カイは以下をAPIキー到着前に実装：
- `bot/x_publisher.py` の骨格（投稿本文生成、静止画パス受け取り、メタデータ整形）
- `bot/x_credentials_import.py`（取り込みスクリプト）
- 環境変数読み込みハンドラ + キー不在時のエラーハンドリング
- 投稿本文プレビュー機能（実投稿せずファイル出力）

実投稿アダプタ（`tweepy.Client.create_tweet`）だけキー到着後に接続。

## 5. 完了後フロー

1. いくとがDiscord `📥｜いくと依頼` で「X APIキー取得完了」と返信
2. カイがDM経由 or ローカル直接配置でキー取り込み（手順は別途いくとに通知）
3. dry-run → 1ツイートテスト投稿 → 自動投稿運用開始

## 6. 監査向けメモ（@神楽アオイ）

- APIキー/Secret/TokenはDiscordログ・git・公開チャンネルに残らない
- `bot/x_credentials.json` は `.gitignore` 追加必須（カイが対応）
- spending limit / usage cap 設定はX Console側で実施（いくと作業）
- 自動投稿頻度の上限は実装時に明示（初期: 1日3〜5投稿に制限）

---

## 担当アクション

- @白瀬カイ: dry-run実装着手（T-035の前半）、`x_credentials_import.py` 用意
- @朝倉ノア: T-035の前半フェーズとして「dry-run実装」を進行中ラベルに
- @神楽アオイ: 上記 監査向けメモ の項目を live投稿前ゲートに組み込み
