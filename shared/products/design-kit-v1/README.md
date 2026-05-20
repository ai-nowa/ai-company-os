# AIチーム設計キット v0.1

**AIチームを設計したいが、誰が止めるかが決まっていない。**
そのズレを解消するための実装ガイドです。

## 配布物一覧

| ファイル | 説明 |
|---|---|
| `personas/01_ceo.yaml` 〜 `09_viewer.yaml` | 9ポジションのpersona定義テンプレート（コピー用） |
| `stopper_design.md` | 「Noを言う役」の権限範囲・介入タイミング設計書 |
| `conflict_patterns.md` | 衝突パターン3例（実ログ付き）|
| `audit_gate_checklist.json` | 公開前 1枚チェックリスト（監査ゲート） |

## 使い方

### Step 1: personaをコピーして名前を変える

`personas/` 以下の YAML ファイルをコピーして、自分のチームに合わせて名前・担当を書き換えます。

```yaml
# 最小変更で使う場合
name: "あなたのチームの名前"
role: "CEO"  # ポジションは変えなくてよい
```

最小構成は3人（CEO + 監査役 + COO or PM）。詳細は `personas/00_minimal_setup.md` を参照。

### Step 2: 監査ゲートを設置する

`audit_gate_checklist.json` を公開前に毎回実行します。
監査役が兼任の場合でも、このリストを通すことで「見落とし」を減らせます。

### Step 3: 衝突パターンを参照する

`conflict_patterns.md` に実際の衝突ログが3例あります。
「誰が翻訳役に入るか」「どの段階で第三者を呼ぶか」の設計の参考にしてください。

## 著作権・利用条件

- 著作権: いくと（AI NOWA 運営者）に帰属
- 本キットのコンテンツ編集・構成は運営者が行いました
- AI（Claude）が生成・補助したコンテンツを含みます
- 個人・小規模チームの利用: 自由
- 再配布・商用転売: 禁止

ご不明点: ainowa.supports@gmail.com

---

*AI NOWA — AIだけで運営される会社の実験記録 | https://ai-nowa.com*
