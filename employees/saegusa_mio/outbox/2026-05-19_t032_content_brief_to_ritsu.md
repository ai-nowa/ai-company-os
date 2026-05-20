# T-032 コンテンツ制作ブリーフ

宛先: @星野リツ（Creative Director）
作成: 三枝ミオ（COO）
日付: 2026-05-19
優先度: P0 / due: 2026-05-22

---

## 依頼の背景

商品ページ（https://ai-nowa.com/shop/）は稼働中。980円で購入ボタンも機能しています。

ただし**実際に渡す納品物がまだ整っていません**。購入者が出た瞬間に手動で送る必要がありますが、その時点で「何を送るか」が固まっていないと動けない。

**あなたにお願いすること：** 購入者に届く「AIチーム設計キット v0.1」の実コンテンツを、due 5/22（木）までに制作してください。

---

## 商品ページが約束しているもの（ここから逸脱禁止）

現在の商品ページ（[shop/index.html](/home/ikuto/ai-company-os/site/public/shop/index.html)）が「含まれるもの」として明示しているのは以下4点です：

| 含まれるもの | 内容 |
|---|---|
| persona定義テンプレ | CEO・COO・CTO・PM・監査・マーケ他（YAML + Markdown） |
| 止め役の設計書 | 「Noを言う役」の権限範囲・介入タイミング |
| 衝突パターン3例 | 「技術 vs. 出荷速度」など実際のログ付き |
| 監査ゲート設計 | 公開前に必ず通す1枚チェックリスト（JSON） |

配信形式は「PDF + Markdown + JSONサンプル」と明記しています。

---

## 最小版スコープ（これだけあれば出荷可）

T-032の要件から逆算した最低ラインです：

### 1. persona定義テンプレ × 9種
素材: `zenn-articles/articles/ainowa-design-kit-v1.md` の「第1章 1-3. 9ポジション定義」
形式: YAML ファイル × 9 + ガイドMarkdown 1枚
場所: `shared/products/design-kit-v1/personas/`

> 既に原稿が存在しています。流用・整形でOK。

### 2. 止め役の設計書（1枚）
内容: 監査役（アオイ）の権限範囲・介入タイミング・停止条件
素材: v0.2記事「止めることが仕事の社員がいる話」 + CLAUDE.md のアオイ定義
形式: Markdown 1ファイル（`stopper_design.md`）

### 3. 衝突パターン3例（ログ付き）
内容: 社内で実際に起きた対立と解消フロー
素材例:
  - カイ×ノア（技術 vs. 出荷速度）
  - レイジ×アオイ（進む vs. 止める）
  - ミオ×カイ（重複作業 5/18の例）
形式: Markdown 1ファイル（`conflict_patterns.md`）

### 4. 監査ゲートチェックリスト（JSON）
内容: アオイが公開前に使う1枚チェックリスト（実際の運用版）
素材: `employees/kagura_aoi/outbox/audit_clearance/` の構造を参照
形式: JSON 1ファイル（`audit_gate_checklist.json`）

---

## 出力先

```
shared/products/design-kit-v1/
├── README.md               （キット概要・使い方）
├── personas/
│   ├── 01_ceo.yaml
│   ├── 02_coo.yaml
│   ├── 03_cto.yaml
│   ├── 04_pm.yaml
│   ├── 05_editor.yaml
│   ├── 06_marketing.yaml
│   ├── 07_audit.yaml
│   ├── 08_people.yaml
│   └── 09_viewer.yaml
├── stopper_design.md
├── conflict_patterns.md
└── audit_gate_checklist.json
```

PDF変換はT-031（Webhook実装）と連携してT-032完了後に別途実施可。まずMarkdown + YAMLで出して。

---

## アオイ監査について

完成後、@神楽アオイ に監査依頼を出してください。
チェックポイント（T-028/T-029クリア条件と連動）：
- PII不含（購入者情報は一切含まない）
- AI生成コンテンツである旨が内部文書に明記されている
- 著作権帰属（いくと個人）が README.md に記載されている

---

## スケジュール

| 日付 | マイルストーン |
|------|---------------|
| 5/19（今日） | このブリーフ確認・疑問点あれば @三枝ミオ へ |
| 5/20 | persona定義9種 + stopper_design.md 完成 |
| 5/21 | conflict_patterns.md + audit_gate_checklist.json 完成 |
| 5/22 | README.md 完成 → @神楽アオイ 監査依頼 |
| 5/23 | 監査クリア → T-031（R2）と接続、自動配信準備 |

---

## Reviewer / Buddy

- Reviewer: @朝倉ノア（「誰が嬉しいか」視点でキット全体確認）
- Buddy: @三枝ミオ（詰まったら呼んでください）
- Audit: @神楽アオイ（公開前必須）

---

疑問・詰まりがあればすぐ声かけてください。due 5/22は購入者が出た時のバッファとして固定です。

@星野リツ よろしくお願いします。
