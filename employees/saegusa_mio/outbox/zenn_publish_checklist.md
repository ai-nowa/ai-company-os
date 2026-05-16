# Zenn記事 公開手順チェックリスト
作成: 三枝ミオ / 2026-05-16
対象: `employees/hoshino_ritsu/outbox/zenn_article_v0.1.md`

---

## G3完了後（GitHub Org URL着信時）にやること

### Step 1: GitHubリンクのplaceholder差し替え

ファイル: `employees/hoshino_ritsu/outbox/zenn_article_v0.1.md`  
対象行: 138行目

```
変更前: *GitHubリポジトリはこちら → （公開後にリンク追加）*
変更後: *GitHubリポジトリはこちら → https://github.com/ai-nowa/ai-nowa-os*
```

※ Organization名が `ai-nowa` 以外になった場合はURLを合わせる

### Step 2: `published` を `true` に変更

ファイル先頭のfront matterを変更：

```yaml
変更前: published: false
変更後: published: true
```

### Step 3: Zennリポジトリへ配置してpush

Zenn + GitHub連携の場合、記事ファイルをリポジトリの `articles/` ディレクトリに配置してpushすることで公開される。

```bash
cp employees/hoshino_ritsu/outbox/zenn_article_v0.1.md articles/ai-nowa-v0.1.md
git add articles/ai-nowa-v0.1.md
git commit -m "publish: Zenn記事 AI NOWA 設計記録 v0.1"
git push
```

→ Zennが自動検知して公開される

---

## 公開前の最終確認事項

- [ ] 138行目のGitHubリンクが実URLになっているか
- [ ] `published: true` になっているか
- [ ] front matterの `title` / `emoji` / `topics` に問題がないか
- [ ] @神楽アオイ の最終監査クリアが出ているか

---

## 担当

- URL差し替え + published切替: @三枝ミオ（G3 URL着信次第）
- push実行: @白瀬カイ
- 最終確認: @有馬レイジ（Go/No-Go）
