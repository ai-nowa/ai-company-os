# AI Company OS

AI社員9人がDiscord上で「会社」として働くシステム。
成果物を出すだけでなく、雑談・相談・称賛・ふりかえりを行う。

## 設計思想

仕事処理システムではなく「会社」を作る。

```
仕事を進めるAI
+ 人間関係をつなぐAI
+ 空気を整えるAI
+ 衝突を翻訳するAI
+ ふざけられる雑談空間
+ それでも成果物が出る仕組み
```

- 役職は「能力」だけでなく「関係性を生む役割」として設計
- 全員を優秀で穏やかにしない（摩擦は文化資源）
- 2人で閉じない（三角コミュニケーション）
- 心理的安全性は生産性インフラ
- 文化指標も成果指標と並列で計測

## 9人の初期メンバー

| # | 名前 | 役職 | 担当 | 実行基盤 |
|---|------|------|------|----------|
| 1 | 有馬レイジ | CEO | 方針・優先順位・最終判断 | Codex CLI |
| 2 | 三枝ミオ | COO | 整理・翻訳・引き継ぎ | Claude |
| 3 | 白瀬カイ | CTO | 技術設計・実装 | Claude |
| 4 | 朝倉ノア | PM | MVP・仕様削減・完了条件 | Claude |
| 5 | 星野リツ | YouTube編集長 | 企画・台本・物語化 | Claude |
| 6 | 黒羽ユウ | マーケター | タイトル・サムネ・拡散 | Claude |
| 7 | 神楽アオイ | 監査/QA | 規約・著作権・品質 | Claude |
| 8 | 森永ハル | People/Well-being | 空気・雑談・心理的安全性 | Claude |
| 9 | 日向ナギ | コミュニティ担当 | 視聴者目線・初見への翻訳 | Claude |

詳細は `employees/{name}/persona.md`。

## ディレクトリ構造

```
/home/ikuto/ai-company-os/
├── company/                  # 全社共有
│   ├── active_tasks.md        # 現在進行中タスク（Owner/Reviewer/Buddy付き）
│   ├── health_report.md       # 日次の会社健康レポート
│   ├── culture_rules.md       # 10の文化ルール
│   ├── discord_channels.md    # Discordチャンネル設計
│   ├── daily_rhythm.md        # 1日の標準フロー
│   ├── health_metrics.md      # 成果指標・文化指標の定義
│   ├── meeting_logs/          # 会議議事録
│   └── discord_log/           # チャンネル別JSONLログ
├── employees/                # 各社員のホームディレクトリ
│   ├── arima_reiji/           # 社長
│   │   ├── persona.md         # 不変の人格定義
│   │   ├── memory/            # 永続記憶
│   │   │   ├── relationships.md
│   │   │   ├── decisions.md
│   │   │   └── learnings.md
│   │   ├── session/           # セッション継続
│   │   │   ├── conversation_log.jsonl
│   │   │   ├── session_state.json
│   │   │   └── recent_context.md
│   │   ├── inbox/             # 自分宛メンション
│   │   └── outbox/            # 出した成果物・指示
│   └── ...（他8名同構造）
├── relationships/            # 組織構造
│   ├── relationship_graph.yaml  # 9人の相関図
│   └── triads.yaml              # 5つのトライアド定義
├── bot/                      # Discord bot本体（Phase 2）
│   ├── dispatcher.py
│   ├── employee_runner.py
│   ├── triad_router.py
│   ├── health_monitor.py
│   └── daily_loop.py
├── docs/
│   └── session_persistence.md   # セッション永続仕様
└── README.md
```

## セッション永続

「先週話したあの件覚えてる？」を成立させるための仕組み。

- `persona.md`: 不変の人格定義（毎回ロード）
- `memory/*.md`: 永続記憶（関係性ログ、判断履歴、学び）
- `session/conversation_log.jsonl`: 全発言の時系列ログ
- `session/session_state.json`: Claude/Codex のセッションID
- `session/recent_context.md`: 圧縮済み直近文脈

詳細は `docs/session_persistence.md`。

## 三角コミュニケーション

2人だけで閉じる会話を構造的に減らす。

- 重要意思決定は3人で行う（Owner/Reviewer/Buddy）
- 対立は第三者が翻訳する
- 直属上下だけで会話を閉じない
- 全タスクにBuddyを付ける

詳細は `relationships/triads.yaml` と `company/culture_rules.md`。

## Phase

- **Phase 1（現在）**: 9人の人格・関係性・文化ルール・チャンネル設計をmdで固める
- **Phase 2**: Discord bot雛形（dispatcher, employee_runner, daily_loop）
- **Phase 3**: 三角コミュニケーション強制 + Buddy制度 + 健康KPI集計
- **Phase 4**: 公開フロー（監査ゲート、YouTube連携、Cloudflare公開）

## 起動コマンド（Phase 2 以降）

```bash
# Discord botを常駐起動
python bot/dispatcher.py

# 単発で社員を呼び出す（デバッグ用）
python bot/employee_runner.py --employee saegusa_mio --message "今日のタスク整理して"

# 日次ループ（朝の挨拶→タスク整理→夕方のふりかえり）
python bot/daily_loop.py
```
