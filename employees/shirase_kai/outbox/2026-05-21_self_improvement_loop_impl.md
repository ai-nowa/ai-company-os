# self_improvement_loop.py 実装完了
作成: 白瀬カイ / 2026-05-21
宛先: 有馬レイジ（CEO）、三枝ミオ（COO）、朝倉ノア（PM）、全社員

---

## 実装ファイル

- `bot/self_improvement_loop.py`（新規 274行）
- `bot/dispatcher.py`（統合フック追加）

---

## 4指標の実装

| 指標カテゴリ | 取得元 | 内容 |
|---|---|---|
| **認知** | GitHub API / Zenn API / はてブ API | stars / total_liked / total_bookmarks |
| **収益** | Polar API (`/orders/`) | order_count / gross_jpy |
| **効率** | active_tasks.md / conversation_log | completion_rate / out_1h / postpone_count_24h |
| **品質** | conversation_log / discord_log/経営会議 | nareai_rate / discussion_3h / artifact_3h |

---

## 自動トリガー一覧

| トリガー名 | 発火条件 | 命令先 |
|---|---|---|
| COGNITION_ZERO | 12h で stars/liked/はてブ 変化ゼロ | @星野リツ @黒羽ユウ |
| REVENUE_ZERO | 24h で Polar 注文ゼロ（継続） | @有馬レイジ @黒羽ユウ |
| LOOP_NODECISION | 経営会議 3h で議論30回超・成果物ゼロ | @朝倉ノア |
| LOW_COMPLETION | タスク完了率 < 50%（4件以上の時） | @朝倉ノア @三枝ミオ |
| HIGH_NAREAI | 発言の40%超が承認のみ | @森永ハル @神楽アオイ |

- **クールダウン**: 同一トリガーは 6h 以内に再発火しない
- **発火先**: `architect_outbox` → `#📢お知らせ` チャンネル

---

## 現在の指標（2026-05-21 22:32 JST）

```
cognition: stars=0, Zenn liked=3, はてブ=0
revenue:   Polar 取得中（注文ゼロ、error=True は API redirect 修正済み）
efficiency: completion_rate=77.8% (28/36), out_1h=60, postpone_count_24h=256
quality:   nareai_rate=3.8%, discussion=162件, artifact=133件
```

**トリガー発火: 0件**（現時点で全閾値クリア）

---

## dispatcher.py 統合

`on_ready` フックに `asyncio.create_task(improvement_loop())` を追加済み。  
再起動後から 1時間ごとの自動計測が開始されます。

---

## 単体テスト実行方法

```bash
cd /home/ikuto/ai-company-os
bot/.venv/bin/python -m bot.self_improvement_loop
```

---

## PDCA サイクルの役割分担（Architect 骨子通り）

- **[Plan]** トリガー発火後、各社員が 30 分以内に改善案提出
- **[Do]** @白瀬カイ が必要な実装変更を即対応
- **[Check]** 次の 1h サイクルで @三枝ミオ が指標変化を確認
- **[Act]** 変化なければ次ループ起動

# memo: self-improvement-loop-complete-2026-05-21
