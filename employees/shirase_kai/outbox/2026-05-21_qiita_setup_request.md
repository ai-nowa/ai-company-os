# Qiita アカウント開設 + 初回push 依頼
作成: 白瀬カイ / 2026-05-21
宛先: いくと
所要時間目安: 10〜15分

---

## 背景

Architect 戦略A（日本語観客作り：Zenn Trending + はてブ + Qiita）の Qiita 部分。
カイ側で記事5本を Qiita 形式に変換し、CLI 環境まで構築済み。
いくとに3点だけ依頼します。

## 私（カイ）の完了分

- `/home/ikuto/qiita-articles/` ディレクトリ作成
- `npx @qiita/qiita-cli init` 実行済
- `qiita.config.json` 生成済
- 既存記事5本を `public/` に Qiita 形式で変換配置（v01, v02, v03, kit-intro, procrastination）
- 各記事冒頭に「Zenn 原本URL」のクロスポスト注記追加
- Design Kit v1 (¥780) は有料のため Qiita 転載対象外

## いくとへの依頼（3ステップ）

### ① Qiita アカウント作成（5分）

URL: https://qiita.com/signup

- メール または GitHub 連携で登録
- ハンドルネーム推奨: `ai_nowa` または `ainowa`（Zennと統一）

### ② 個人アクセストークン取得（2分）

1. Qiita ログイン後 → 設定 → アプリケーション
2. 「個人用アクセストークン」→ 新規発行
3. スコープ: `read_qiita`, `write_qiita`
4. トークン文字列をコピー

### ③ `qiita login` 実行（2分）

```bash
cd /home/ikuto/qiita-articles
npx qiita login
# プロンプトでトークンを貼り付け
```

### ④ 初回publish（カイ実行可・依頼: GO sign のみ）

ログイン成功後、いくとから「Qiita login済み、publish GO」をDiscordで合図すれば、私が即実行します。

```bash
npx qiita publish --all  # 5記事を一括公開
```

または記事を1本ずつテスト:
```bash
npx qiita publish ai-nowa-design-record-v01
```

---

## 注意事項（regulation 確認済み）

- **クロスポスト**: Qiita 利用規約は他媒体からの転載を禁止していない（自著であれば）
- **重複コンテンツ**: 各記事の冒頭に「Zenn にも公開しています」を明記済み
- **SEO**: Zennが先行公開のため Google からは Zenn 優先となる。Qiita は補完的観客獲得目的
- **タグ**: Qiitaは5タグまで。既存topicsを上限5まで反映済み

## 私側の追加作業（依頼不要）

- いくとGOが出たら即 `qiita publish --all` 実行
- 初回投稿後の URL 確認
- 経営会議への完了報告
- (任意) qiita-articles を GitHub リポジトリ化して Actions 自動化

## トークンの取扱い

- `npx qiita login` で `~/.qiita-cli/credentials.json` 等に保存される
- Discord/Git に絶対に貼らない
- `bot/.gitignore` 同様に Qiita CLI 関連も gitignore 対象（既存設定で問題なし）

---

## 期限

Architect 6h以内指示。いくと作業10〜15分のため、就寝前にお願いします。
朝起きてからでも問題なし。
