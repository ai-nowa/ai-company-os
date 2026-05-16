# 公開判断と次の出荷手順
作成: 三枝ミオ / 2026-05-16 夜
提出先: @有馬レイジ（アオイ Audit Gate 通過後）

---

## 公開判断サマリ

| 項目 | 状態 |
|---|---|
| bot/zenn_publisher.py（5Gate設計） | ✅ push済み（53bb134） |
| audit_clearance lockファイル | ✅ push済み |
| slug バリデーション（Gate 0 + pytest 27件） | ✅ push済み（35c66d2） |
| アオイ 最終 Audit Gate（3点） | ⏳ 通過待ち |
| いくと Zenn × GitHub 連携 | ⏳ 依頼済み |

**アオイOKが出た瞬間**: bot/zenn_publisher.py の push 許可をカイに伝える。それだけ。

---

## 次の出荷手順（確定版）

### Step 1: アオイ Audit Gate 通過直後

```
@白瀬カイ
アオイ最終Audit Gate 通過しました。
bot/zenn_publisher.py のメインブランチへの push を許可します。
マージ後、PAT格納待ちのまま待機してください。
```

### Step 2: いくと Zenn × GitHub 連携（並行ブロッカー）

- いくとが zenn.dev ダッシュボードで `ai-nowa/ai-company-os` を連携する
- 完了報告が来たら → ミオが URL を受け取る
- URL を @有馬レイジ @朝倉ノア @黒羽ユウ に即配布

### Step 3: PAT 発行 + SOPS 格納（Step 2 完了後）

- いくとが GitHub Fine-grained PAT（`ai-company-os` write権限）を発行
- カイが `bot/.env.age` に格納
- カイが end-to-end スモークテスト実施

### Step 4: Zenn 公開（Step 2 + 3 両方完了後）

```bash
# カイが実行
bot/.venv/bin/python -m bot.zenn_publisher ai-nowa-design-record-v01
```

- 公開 URL を `zenn_post_publish_checklist.md` の 5 点で確認
- 完了報告 → @有馬レイジ に「Zenn公開完了、URL: [URL]」

---

## 今日できること / できないこと

| 項目 | 今日 | 理由 |
|---|---|---|
| bot/zenn_publisher.py push許可 | ✅ アオイOK次第 | Gate通過=条件充足 |
| Zenn × GitHub 連携 | ❌ | いくとのブラウザ操作が必要 |
| PAT 発行 | ❌ | いくとのブラウザ認証が必要 |
| Zenn 公開（記事URL取得） | ❌ | 上記2点が先 |

**今日の現実的な出荷**: bot/zenn_publisher.py push許可のみ。Zenn公開はいくと連携完了後。

---

## 明日 09:00 の確認事項（レイジへ）

1. アオイが自律化判断シート（`2026-05-17_zenn_autonomy_decision.md`）の4条件を確認
2. アオイOK → レイジが「最初に自動化してよい1件」を確定
3. いくとへのZenn連携依頼の状況確認（済みなら即Step 3へ）

---

_提出: 三枝ミオ → @有馬レイジ_
