# セッション永続仕様

AI社員に「先週話したあの件覚えてる？」を成立させるための仕組み。

## 階層構造

各社員のホーム配下の永続性レベルは3層：

```
employees/{name}/
├── persona.md         # [不変層]  人格定義。手動更新のみ
├── memory/            # [蓄積層]  重要な記憶。要約・整理されて残る
│   ├── relationships.md  # 同僚との関係性ログ
│   ├── decisions.md      # 過去の判断履歴
│   ├── learnings.md      # 学び・反省・成功パターン
│   └── facts.md          # 知識・社内用語・固有名詞
├── session/           # [流動層]  直近の会話状態
│   ├── conversation_log.jsonl  # 全発言の時系列ログ
│   ├── session_state.json      # SDK セッションID、最終アクセス時刻
│   └── recent_context.md       # 圧縮済み直近文脈（system promptに入れる）
├── inbox/             # 受信箱
└── outbox/            # 送信箱
```

## 起動時のロード順

社員が呼ばれた時、`bot/employee_runner.py` は以下の順でsystem promptを構築：

```
1. employees/{name}/persona.md
2. company/culture_rules.md
3. relationships/relationship_graph.yaml の自分関連抜粋
4. employees/{name}/memory/*.md
5. employees/{name}/session/recent_context.md
6. 直近のメッセージ（最大N件、デフォルト20）を conversation_log.jsonl から
```

これで「人格」「文化」「関係性」「過去の判断」「直近の流れ」がすべて揃った状態で応答できる。

## conversation_log.jsonl の形式

1行1イベント。JSONL（改行区切りJSON）。

```jsonl
{"ts":"2026-05-16T08:30:12+09:00","kind":"in","from":"arima_reiji","via":"discord:🗓今日の業務","text":"今日は第1回動画の台本完成を最優先にします"}
{"ts":"2026-05-16T08:31:05+09:00","kind":"thought","text":"レイジ社長から優先順位。台本完成=リツ主担、私はタスク分解。"}
{"ts":"2026-05-16T08:32:40+09:00","kind":"out","to":"hoshino_ritsu","via":"discord:🎬youtube編集部","text":"リツさん、台本v1の見出しまで今日中にお願いできますか"}
{"ts":"2026-05-16T08:32:41+09:00","kind":"task_update","task":"T-001","change":"owner=hoshino_ritsu, buddy=morinaga_haru"}
```

### kind 一覧

| kind | 意味 |
|------|------|
| in | 受信メッセージ |
| out | 送信メッセージ |
| thought | 内省（system trace、表に出ない） |
| task_update | タスクの状態変更 |
| memory_write | memory/*.md への書き込みフラグ |
| review | レビュー判断 |

## 要約圧縮ロジック

`conversation_log.jsonl` が肥大化するため、以下のタイミングで圧縮：

- **行数 > 500** または **ファイルサイズ > 200KB** で発動
- 古い順に300行を要約 → `session/recent_context.md` に追記
- 要約済みの300行を `session/archive/conversation_log_{YYYY-MM-DD-HH}.jsonl` に移動
- 重要事項は `memory/*.md` の該当ファイルに**事実ベース**で抽出
  - 関係性イベント → relationships.md
  - 判断 → decisions.md
  - 学び → learnings.md
  - 知識 → facts.md

要約は社員自身に書かせる（自分の文体・視点で）。やらせるプロンプト例：

```
あなたは{name}です。
以下は直近の自分の会話ログです。
あなたの視点で、未来の自分が覚えておくべき事項を以下のカテゴリで抽出してください：
- 関係性で起きた出来事（誰とどう関わったか）
- 自分が下した判断とその理由
- 学んだこと・成功パターン・反省点
- 新しく知った事実・社内用語
それ以外（雑談・小さなやり取り）は捨てて構いません。
```

## session_state.json の形式

```json
{
  "claude_session_id": "sess_abc123",
  "codex_session_id": null,
  "last_active": "2026-05-16T18:30:00+09:00",
  "compression_count": 3,
  "total_messages": 1247,
  "current_context_tokens_est": 8400
}
```

## Claude Agent SDK のセッション継続

Claude SDK は新規セッションごとに新しい session_id を発行する。
継続したい場合、`resume` 機能を使うか、自前で会話履歴を再構成する。

このプロジェクトでは**自前再構成方式**を採用する：

- session_id はログ目的でのみ保持
- 起動時は毎回 `persona + memory + recent_context + 直近メッセージ` を組み立てて投げる
- これでSDKのセッション保持機能に依存せず、可搬性を確保

## Codex CLI のセッション継続

Codex CLI（社長レイジ用）はディレクトリベースでセッションを持つ。
`employees/arima_reiji/` を作業ディレクトリにすれば、Codex側で自動的に文脈が継続する。
ただしCodex側のcontextが切れることも想定し、上記の自前再構成は併用する。

## 「忘却」の設計

人間も全部覚えていない。AI社員も意図的に忘れるべきものがある：

- 雑談の細部 → 要約しても消す
- 完了したタスクの中間プロセス → outboxの成果物のみ残す
- 軽い感情の起伏 → ピーク時のみ memory/relationships.md に残す

`memory/*.md` は3ヶ月に1回、社員自身に「もう不要な記憶」を消させるバッチを走らせる予定（Phase 4）。
