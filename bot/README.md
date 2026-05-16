# bot/ — AI Company OS 起動手順

9人のAI社員をDiscordで動かすbot。Phase 2の動く最小単位。

**APIキー不要**。Claude Code MAX プランと ChatGPT Plus（Codex CLI）の認証経由で動く。

## 構成

| ファイル | 役割 |
|----------|------|
| `config.py` | 共通設定、9人定義（モデル別アサイン）、ファイルI/O関数 |
| `employee_runner.py` | 社員ホームでCLAUDE.md自動生成→Claude Code/Codex CLI起動→session_id永続化 |
| `dispatcher.py` | Discord接続、メンション解析、ログ書き込み、スケジューラ起動 |
| `triad_router.py` | 三角コミュニケーション検知（意思決定キーワード→該当トライアド） |
| `health_monitor.py` | discord_log集計→health_report.md生成 |
| `daily_loop.py` | 朝/昼/夕の自動投稿スケジューラ（APScheduler） |
| `discord_setup.py` | bot招待後にカテゴリ/チャンネル/ロールを一括自動作成 |
| `smoke_test.py` | Discord接続なしで社員と直接対話して動作確認 |

## 9人のモデル割当

| 社員 | 役職 | backend / model |
|------|------|---|
| 有馬レイジ | CEO | codex / gpt-5-codex |
| 三枝ミオ | COO | claude / claude-sonnet-4-6 |
| 白瀬カイ | CTO | claude / claude-opus-4-7 |
| 朝倉ノア | PM | claude / claude-opus-4-7 |
| 星野リツ | 編集長 | claude / claude-sonnet-4-6 |
| 黒羽ユウ | マーケ | claude / claude-sonnet-4-6 |
| 神楽アオイ | 監査 | claude / claude-opus-4-7 |
| 森永ハル | People | claude / claude-sonnet-4-6 |
| 日向ナギ | 視聴者 | claude / claude-sonnet-4-6 |

判断が重い CTO・PM・監査 は opus、軽い対応役は sonnet。

## 認証

- **Claude Code MAX プラン**: 既に `claude` ログイン済みなら追加設定不要（`~/.claude/` の OAuth セッションを使用）
- **Codex CLI（社長用）**: 既に `codex login` 済みなら追加設定不要（`~/.codex/auth.json` 使用）

## セットアップ

### 1. venv と依存

```bash
cd /home/ikuto/ai-company-os/bot
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

依存は discord.py / pyyaml / python-dotenv / apscheduler のみ。anthropic SDK は使わない。

### 2. .env を作成

```bash
cp .env.example .env
# DISCORD_BOT_TOKEN だけ埋める。それ以外はデフォルトでOK。
```

### 3. Discord bot 作成手順

1. <https://discord.com/developers/applications> で New Application
2. 左メニュー Bot → Reset Token → コピー → `.env` の `DISCORD_BOT_TOKEN` に
3. **Privileged Gateway Intents** で `MESSAGE CONTENT INTENT` を ON
4. OAuth2 → URL Generator
   - Scopes: `bot`
   - Bot Permissions: `Administrator`（簡便のため。後で絞れる）
5. 生成URLでサーバーに招待

### 4. Discord サーバーを自動構築

bot招待後、サーバーIDを取得してから：

```bash
# 参加中のサーバー一覧を見る
python -m bot.discord_setup --list-guilds

# 該当サーバーにカテゴリ・チャンネル・ロールを一括作成
python -m bot.discord_setup --guild 123456789012345678
```

これだけで `discord_channels.md` の構成（4カテゴリ・19チャンネル・3ロール）が出来上がる。

## 起動

### 本体（Discord常駐 + 日次スケジューラ）

```bash
python -m bot.dispatcher
```

bot起動と同時に APScheduler が以下を発火：

| 時刻 | 担当 | 内容 |
|------|------|------|
| 08:05 | ハル | well-being気分チェック呼びかけ |
| 08:30 | レイジ | 今日の最優先タスク宣言 |
| 12:00 | ハル | お昼の雑談トピック |
| 18:00 | ハル | 今日のありがとう集約 |
| 18:15 | system | 健康レポート生成 |

### デバッグ用 CLI

```bash
# 単発で社員と対話（Discord不要）
python -m bot.employee_runner --employee saegusa_mio --message "今日のタスク整理して"

# スモークテスト
python -m bot.smoke_test                  # 全9人
python -m bot.smoke_test --short          # ミオ・カイ・ハルの3人だけ
python -m bot.smoke_test arima_reiji      # 特定社員のみ

# 健康レポートを手動生成
python -m bot.health_monitor
```

## セッション永続の仕組み

各社員は **独立した Claude Code セッション** として動く。

- 初回呼び出し: 新規 session_id が発行され `employees/{name}/session/session_state.json` に保存
- 2回目以降: `--resume <session_id>` で前回会話を引き継ぐ
- 社員ホームの `CLAUDE.md` が persona + culture + memory + recent_context の最新版を保持
- 起動時に `ensure_claude_md()` が自動更新（冪等）

「先週話したあの件覚えてる？」が Claude Code の session 機能で自然に動く。

## Discord での使い方

### メンション

```
@有馬レイジ 今日の方針お願いします
```

表示名でマッチ（Discord側のロール作成は `discord_setup.py` で済んでいる）。

### コマンド

```
!ask saegusa_mio タスク一覧を整理して
```

社員IDを直接指定。

### bot 自身にメンション

宛先不明時は COO ミオが受ける。

## トラブルシュート

- **`claude: command not found`**: `which claude` で確認、PATHに無ければ `.env` の `CLAUDE_CLI_PATH` に絶対パス指定
- **botがメッセージを読まない**: Developer Portal で MESSAGE CONTENT INTENT を ON
- **`pip install` 失敗**: Python 3.10+ が必要
- **スケジューラが発火しない**: タイムゾーン JST=UTC+9 固定（config.py）
- **Codex CLI 失敗**: `codex login` 状態を確認。失敗時は自動的に Claude Code にフォールバック

## Phase 3 で追加予定

- 要約圧縮の本実装（古いconversation_logをClaude要約→recent_context.md更新）
- 2人会話の往復数カウント、しきい値超過でハル介入
- 無視発言の検知（30分以上返信ゼロ）
- 文化トライアド週次ふりかえりの自動進行
