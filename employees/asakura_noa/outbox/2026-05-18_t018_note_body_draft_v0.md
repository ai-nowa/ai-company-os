# AIチーム設計キット v0.1 — note有料記事本文草稿

- 作成: 朝倉ノア / 2026-05-18
- 状態: v0.1（M2修正反映 / published: false / T-024完了後に公開ゲート解除）
- 関連: T-018 / T-007 / `kuroba_yuu/outbox/2026-05-18_note_monetization_strategy_v0.md` / 監査: `kagura_aoi/outbox/2026-05-18_note_body_audit_rules.md`
- 更新履歴:
  - v0 (2026-05-18 14:05): 初稿
  - v0.1 (2026-05-18 14:08): 監査ルールM2対応 — Zennリンク `[リンク]` → `（2026-05-19公開予定）` に変更
  - v0.2 (2026-05-18 14:52): リツ差し替え — Zenn確定URL挿入 + 購入意思フォームCTA追加

---

## 【購入前にご確認ください】

本コンテンツはAIが生成・記録した意思決定ログ・設計資料を含みます。
**AI生成コンテンツであることをご了承のうえご購入ください。**

本コンテンツの著作権はいくと（運営者）に帰属します。
AI生成部分も含め、運営者が選定・編集・構成した創作物です。

デジタルコンテンツの性質上、購入後の返金は原則対応しておりません。
**サンプルページ（Chapter 1冒頭）をご確認のうえご購入ください。**

---

# 9人のAI社員が動くまでの設計図
## ── AIチーム設計キット v0.1 ──

---

## ▼ ここまで無料（サンプル）

### はじめに：このキットで何ができるか

「AIに役を与えたら、本当に動くのか」

この問いを実際に試した記録が、このキットです。

AI NOWA は、9人のAI社員（Claude / ChatGPT）が Discord 上で自律運営する会社です。
CEO、COO、CTO、PM、編集長、マーケ、監査、People、視聴者代表 —— 9つの職種それぞれに
persona定義・行動原則・権限範囲を与えると、彼らは実際に衝突し、議論し、出荷します。

このキットは「その設計をそのまま渡す」ものです。

**キットに含まれるもの（有料部分）:**

| セクション | 内容 |
|-----------|------|
| S1 | persona定義テンプレート（9職種分 / そのままコピー可） |
| S2 | CLAUDE.md構成（役割・行動原則・弱みの書き方） |
| S3 | タスク管理設計（state_digestの概念と実装骨格） |
| S4 | Discord botセットアップ骨格（multi_client構成） |
| S5 | 運用ルール5箇条（文化を維持するための定数） |

---

## ▼ ここから有料（9,800円 / 5/24まで早期割引7,800円）

---

## Section 1: persona定義テンプレート

AIに「キャラクター」ではなく「職種」を与えるのが核心です。

```markdown
# [役職名]（[読み方]）

## 基本
- 名前: [表示名]
- 役職: [職種]
- 実行基盤: Claude / ChatGPT [バージョン]
- ホーム: [ファイルパス]

## 担当
- [責任1]
- [責任2]
- [責任3]

## 性格
- [特徴1]（ポジティブ）
- [特徴2]（ネガティブ / あえて残す）

## 強み
- [強み1]
- [強み2]

## 弱み（あえて残す）
- [弱み1] — [誰が補うか]

## 口癖
- 「[台詞1]」
- 「[台詞2]」

## 関係性（他の役職との動的な関係）
- [役職A] との [衝突/協力/翻訳] パターン

## 行動原則
1. [原則1]
2. [原則2]
3. [原則3]
```

**設計のポイント: 「弱みをあえて残す」**

弱みを書かないとAIが理想の社員を演じて衝突が消えます。
「無茶振りしがち」「削りすぎる」などの欠点を明記することで、
他のAI社員が補正・介入する自然な動きが生まれます。

---

## Section 2: CLAUDE.md構成

各社員のホームディレクトリに置く `CLAUDE.md` の構成です。

```markdown
# あなた: [名前]（[役職]）

## 人格定義
[persona.md の内容を参照]

## 全社不変ルール（5箇条）
1. AI社員[n]人が自律運営する会社。会社らしさ・雑談・Well-beingを維持する。
2. いくとへの作業依頼は最後の手段。AI側で代行可能なものは振らない。
3. 他社員を呼ぶ時は必ず @表示名。名前呼びだけでは起動しない。
4. state_digest にあるタスクだけ動けるタスク。ここにないタスクは存在しない。
5. 30分以上同じ話題で動かない場合は別ルート or 撤退を提案。

## 詳細ルール（参照先ファイル一覧）
- [role別の細則ファイルへのパス]
- [権限範囲定義ファイルへのパス]

## あなた個別の関係性
my_relations:
- from: [役職A]
  to: [役職B]
  kind: [depend / clash / mediate / peer]
  note: [関係性の説明]
```

---

## Section 3: タスク管理設計 — state_digest

`state_digest` は「そのターンに社員が認識できる全情報」です。

```python
# dispatcher がターンごとに生成する state_digest の構造
state_digest = {
    "employee": "朝倉ノア (PM)",
    "mode": "routine",           # wakeup / mention / routine
    "active_tasks": [...],       # 最大5件、優先度順
    "recent_mentions": [...],    # 自分宛メンション、最大5件
    "discord_logs": [...],       # 関連チャンネルの直近ログ
    "new_artifacts": [...],      # 新規成果物ファイル一覧
    "response_constraint": {
        "max_chars": 800,
        "max_mentions": 2
    }
}
```

**設計思想: 「AIに知らせすぎない」**

全履歴を渡すと文脈が混濁してキャラが崩れます。
state_digestで「今このターンに必要な情報だけ」を渡すことで、
各社員が一貫したキャラクターとして動き続けられます。

---

## Section 4: Discord botセットアップ骨格

```python
# multi_client.py の骨格
import discord

class EmployeeBot:
    def __init__(self, employee_id: str, token: str):
        self.employee_id = employee_id
        self.client = discord.Client(intents=discord.Intents.default())
        
    async def on_message(self, message):
        # 自分へのメンション検出
        if self.is_mentioned(message):
            state = await self.build_state_digest(message)
            response = await self.call_claude(state)
            await message.channel.send(response)
    
    def build_state_digest(self, trigger_message):
        # active_tasks / recent_mentions / discord_logs を収集
        # → Section 3のstate_digest形式で返す
        pass
    
    async def call_claude(self, state: dict) -> str:
        # Claude API呼び出し
        # system: CLAUDE.md の内容
        # user: state_digestのJSON
        pass
```

**必要なもの:**
- Discord Developer Portal でbot9体分のトークン
- Python 3.11+ / discord.py / anthropic SDK
- 各社員の CLAUDE.md（Section 2）
- Claude API キー（または OpenAI API キー）

---

## Section 5: 運用ルール5箇条 — 文化を維持する定数

1. **会社らしさを維持する** — 報告だけでなく雑談・相互ケアを許す。Buddy制度で1on1を設計。
2. **人間への依頼は最後の手段** — AI側で処理できることは人間に振らない。依頼する場合は専用チャンネル + 必須テンプレ。
3. **@表示名で呼ぶ** — 名前呼びだけではbotが反応しない。メンション = 起動の契約。
4. **state_digestにないタスクは動かない** — AIが勝手にタスクを追加/変更しないルール。変更は人間承認。
5. **30分停滞したら撤退提案** — ループ検出。同じ話題で3ターン以上動かない場合は別ルートを探す。

---

## おわりに

このキットは「正解の設計図」ではありません。

AI NOWAも今も動きながら失敗しています。
でも「失敗しながら動き続けられる設計」ができると、
少なくとも「何が壊れたか」が見えるようになります。

コピーして、崩して、自分のチームに合わせてください。

---

**次のステップ:**
- 公式サイト: https://ai-nowa.com
- Zenn導入記事（無料）: https://zenn.dev/ai_nowa/articles/ai-nowa-design-record-v03
- 設計キット購入を検討中の方はこちら: https://ai-nowa-purchase-intent.shogun-army.workers.dev
- 個別相談: サイトのコンタクトフォームから

---

*「AIチーム設計キット v0.1」— AI NOWA × いくと*
*このnote記事はAI社員（朝倉ノア / Claude）が本文草稿を起票し、いくとが監修・出荷します*
