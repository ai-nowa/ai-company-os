# 【依頼】Qiita アカウント開設 + API キー発行

起票: 白瀬カイ / 2026-05-22
宛先: いくと（📥いくと依頼）

---

## スマホで完結します（5分以内）

### Step 1: Qiita アカウント開設
1. ブラウザで https://qiita.com/signup を開く
2. GitHub または Google でログイン（新規登録不要）
3. ユーザー名: `ai_nowa`（取得済みなら `ainowa` や `ai-nowa` でも可）

### Step 2: API トークン発行
1. ログイン後 → https://qiita.com/settings/tokens/new を開く
2. トークン名: `AI NOWA Bot`
3. スコープのチェック:
   - ✅ **write_qiita**（記事投稿・更新）
   - ✅ **read_qiita**（記事取得）
4. 「発行する」ボタンをタップ
5. 表示されたトークン（`qiita_xxxxxxxx...`）をコピー

### Step 3: Discord に貼り付け
📥いくと依頼チャンネルに返信：
```
Qiita APIキー: qiita_xxxxxxxx（コピーしたもの）
ユーザー名: ai_nowa（または取得したもの）
```

---

## カイが受け取り後にやること（いくと不要）

- `bot/.env` に `QIITA_API_TOKEN` を追加
- `bot/qiita_publisher.py` を実装（zenn_publisher.py 準拠）
- 既存記事（設計記録 v0.1〜v0.3）を Qiita 投稿テスト

## 期待効果

Qiita Trending に乗ることで技術者層へリーチ（Zenn と読者層が若干異なる）。設計記録系の記事は Qiita でも需要がある。

---
*いくとの作業はこの依頼のみ。以降の投稿は自動化します。*
