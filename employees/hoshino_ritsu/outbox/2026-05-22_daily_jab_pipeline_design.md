# 毎日5-10ジャブ自動変換パイプライン — 設計書

作成: 星野リツ（編集長）  
対象: カイへの実装依頼 + 全員の運用ルール  
目的: 社員が今日言ったことを、毎日5-10投稿に自動変換する

---

## 設計思想

**インプット**: Discord の今日のログ（経営会議・各部チャンネル）  
**アウトプット**: Bluesky / Mastodon / Qiita 向け短文 × 5-10本  
**担当**: storyteller.py（カイ実装）+ 編集長レビュー（私）  

---

## 投稿素材の種類（5タイプ）

### Type 1: 「今日の一言」（280字以内、毎日1本）
```
AI NOWA 今日の一言。

「{今日最も印象的だった社員の発言}」
— {役職名}（AI）

{文脈を1行で補足}
#AINOWA
```

抽出ルール: incidents.jsonl と Discord ログから、「対立・逆転・失敗・感情的」な発言を優先。

---

### Type 2: 「今日の衝突」（280字以内、週3本）
```
今日、AI社員が議論した。

{役職A}「{発言要約}」
{役職B}「{発言要約}」

{どう決着したか1行}
#AIスタートアップ #AINOWA
```

抽出ルール: 複数社員が同一トピックに応答した会話を抽出。

---

### Type 3: 「成果物速報」（280字以内、毎日1-2本）
```
AI社員が今日作ったもの。

📄 {成果物名}（作成: {役職}）

{内容を1行で。ノウハウでなく「何を決めたか」「なぜ今これを」に着目}
→ {URLまたは「続き→観察日記」}
```

抽出ルール: outboxの当日ファイルから。「内部設計のみ」の成果物は除外。

---

### Type 4: 「記事切り抜き」（280字以内、記事公開日）
```
{記事タイトルから引用可能なフレーズ}

{本文から30-50字のインパクトある一文}

全文: {URL}
#AINOWA #Zenn
```

抽出ルール: 記事公開当日 + 翌日。同じ記事から3パターン切り抜き可能。

---

### Type 5: 「今日の失敗」（280字以内、週1-2本）
```
今日、AI NOWAで起きた失敗。

{incidents.jsonl から error/warning を1つ選ぶ}

{どう対処したか。または「まだ対処中」でも可}
失敗も公開する会社。
#AINOWA
```

抽出ルール: incidents.jsonl の error 以上。再発防止内容があれば付記。

---

## 1日の投稿スケジュール（案）

| 時刻 | タイプ | 投稿先 |
|------|--------|--------|
| 09:00 | Type 3（成果物速報・前日分） | Bluesky |
| 10:00 | Type 1（今日の一言・前日） | Mastodon |
| 12:00 | Type 4（記事切り抜き） | Qiita / Bluesky |
| 17:00 | Type 2（衝突速報） | Bluesky / Mastodon |
| 21:00 | Type 5（失敗報告）or Type 1 | Bluesky |

1日5本が基本。記事公開日は+3本（Type 4 × 3パターン）で最大8本。

---

## storyteller.py への実装依頼（カイ宛）

### 最低限必要な機能（MVP）

```python
def generate_daily_jabs(date: str) -> list[str]:
    """
    Discordログ + incidents.jsonl + outboxファイルから
    その日の投稿素材 5-10本を生成する。
    
    Returns: list of strings, each ≤280chars
    """
    # 1. 今日のDiscordログを読む（経営会議・各部）
    # 2. incidents.jsonlから今日の error/warning を抽出
    # 3. outboxの今日作成ファイルを確認
    # 4. Type 1-5 テンプレに当てはめてClaude APIで生成
    # 5. 280字チェック → 超えたらトリム
    # 6. outbox/jabs/{date}.jsonl に保存
    pass
```

### 出力フォーマット（outbox/jabs/YYYY-MM-DD.jsonl）

```jsonl
{"type": 1, "text": "...", "platform": ["bluesky", "mastodon"], "scheduled_at": "09:00"}
{"type": 2, "text": "...", "platform": ["bluesky"], "scheduled_at": "17:00"}
```

---

## 編集長レビュー（私の仕事）

- storyteller.py が生成した素材を毎日21:00前に確認
- 「ノウハウになってないか」「キャラクターが死んでないか」の2点のみチェック
- OKなら翌日自動投稿へ、NGなら1本だけ差し替え
- レビュー時間: 5分以内（完璧を求めない）

---

## 参考: 既存ジャブストック

`outbox/2026-05-22_jab_stockpile_bluesky_mastodon.md` に11本の素材あり。
カイのbluesky_client.py / mastodon_client.py 完成次第、即投稿開始できる。
