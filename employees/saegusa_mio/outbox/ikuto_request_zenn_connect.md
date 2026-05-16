## 【依頼: Zennダッシュボード連携 + 記事公開実行】

### なぜ必要か
bot/zenn_publisher.py の実装・テスト・Gate確認が全て完了しています。
唯一残っているのは「Zennダッシュボードでai-nowa/ai-company-osを連携する」いくとのブラウザ操作のみです。
これが完了すれば即座にZenn記事が公開できます。

### 詳細手順（そのまま実行できる粒度）

**Step 1: Zennダッシュボード連携（約3分）**
1. https://zenn.dev にログイン（ai-nowaアカウント）
2. 右上アイコン → 「GitHubからのデプロイ」
3. 「リポジトリを連携する」→ `ai-nowa/ai-company-os` を選択
4. 「articles/」ディレクトリを指定して保存

**Step 2: 記事公開スクリプト実行（約1分）**
```bash
cd /home/ikuto/ai-company-os
bot/.venv/bin/python -m bot.zenn_publisher ai-nowa-design-record-v01
```

**Step 3: 公開URL確認**
- スクリプト実行後に表示されるURLをそのまま @三枝ミオ に共有してください

### 期待される結果
- Zenn記事「AI NOWA 設計記録 v0.1」が公開状態になる
- 公開URLが取得できる

### 完了時の報告先
@三枝ミオ に公開URLを共有 → レイジ・ノア・ユウへ即配布します

### 緊急度
**即時**（今日の最優先出荷）

### 起票者
@三枝ミオ
