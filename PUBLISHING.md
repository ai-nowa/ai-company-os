# 公開リポジトリ準備手順

このリポジトリを GitHub 上で公開する際の手順。
**監査担当 kagura_aoi の G4（公開前リスク確認）を通過した後**、いくとが実行する。

---

## 1. 公開対象 / 非公開対象

### 1.1 公開する（明朝アオイG4で確認）

| パス | 内容 |
|---|---|
| `bot/*.py`（`.env` 除く） | Discord bot のコード |
| `bot/requirements.txt` | 依存パッケージ |
| `employees/*/persona.md`, `CLAUDE.md` | 9人の人格定義 |
| `employees/*/memory/*.md` | 永続記憶（事実・決定・学び） |
| `employees/*/outbox/` | 公開成果物 |
| `company/*.md` | ミッション・文化ルール・ポリシー |
| `relationships/`, `docs/` | 構造・仕様書 |
| `shared/templates/`, `shared/docs/`, `shared/articles/` | テンプレート・公開判定ポリシー・記事 |
| `founders/*/persona.md`, `CLAUDE.md` | 創業者プロフィール |
| `founders/*/memory/`, `outbox/` | 創業者の判断履歴・成果物 |
| `README.md`, `PUBLISHING.md`, `.gitignore` | リポジトリ運用 |

### 1.2 公開しない（`.gitignore` 対象）

| パス | 理由 |
|---|---|
| `bot/.env` | Discord トークン・API 鍵 |
| `bot/.venv/`, `__pycache__/` | 環境ファイル |
| `employees/*/session/conversation_log.jsonl` | 個別会話ログ |
| `employees/*/session/session_state.json` | セッションID |
| `employees/*/session/recent_context.md` | 直近文脈圧縮（社内のみ） |
| `employees/*/session/archive/` | 旧セッション |
| `company/discord_log/` | Discord 全チャンネルログ（→G4でアオイが選別公開を別途検討） |
| `company/incidents.jsonl` | インシデント記録 |
| `company/thread_registry.json` | スレッド管理（社員IDマップ含む） |
| `founders/*/session/` | 創業者の会話履歴 |

### 1.3 要監査（明朝アオイG4で判定）

| パス | 論点 |
|---|---|
| `employees/*/inbox/` | 現状空。今後の運用で機密が入る可能性、ポリシー要決定 |
| `founders/ikuto/memory/`, `outbox/` | 人間創業者の個人情報含む可能性 |
| `shared/data/`, `shared/archive/` | 内容次第 |

---

## 2. 公開前のチェック（カイがG1で実行 → 明朝アオイG4で再確認）

### 2.1 シークレットスキャン

全 git 履歴を対象に：

```bash
# trufflehog（推奨。github API キー、AWS、JWT 等を検出）
trufflehog filesystem /home/ikuto/ai-company-os --no-update

# git-secrets（簡易・補助）
cd /home/ikuto/ai-company-os
git secrets --scan-history
```

### 2.2 孤立ref / 過去コミットのチェック

```bash
cd /home/ikuto/ai-company-os
git fsck --unreachable --no-reflogs
git log --all --full-history --source -- bot/.env  # 過去に .env が含まれていないか
```

### 2.3 平文の認証情報 grep

```bash
cd /home/ikuto/ai-company-os
grep -rIE "(DISCORD_TOKEN|API_KEY|SECRET|PASSWORD|sk-[A-Za-z0-9]{20,})" \
  --exclude-dir=.git --exclude-dir=.venv --exclude-dir=__pycache__ . || echo "OK: no plaintext secrets"
```

---

## 3. 初回push手順（いくとが実行）

> **前提**: 上記2のシークレットスキャンが通り、アオイG4が承認済み。

1. **GitHub Organization 作成**
   - `AI-NOWA` を Organization として作成（いくとが Owner）
2. **リポジトリ作成**
   - 名称: `ai-company-os`（または三枝ミオ・アオイ確認後の名称）
   - **Visibility は初回 Private** で作成
3. **ローカルから push**
   ```bash
   cd /home/ikuto/ai-company-os
   git remote add origin git@github.com:AI-NOWA/ai-company-os.git
   git branch -M main   # master → main へ
   git push -u origin main
   ```
4. **Private 状態でアオイ最終確認**
   - GitHub UI 上で全ファイルを目視確認
   - 問題なければ Settings → Visibility → **Public** に切替
5. **公開完了の記録**
   - `company/active_tasks.md` に「公開完了」を記入
   - `📦成果物報告` に URL を投稿

---

## 4. 失敗時のロールバック

- Public 切替後に問題が発覚した場合：
  1. 即座に Visibility → Private に戻す（GitHub上の検索インデックス削除には別途申請が必要）
  2. 該当ファイルを削除し、`git filter-repo` で履歴からも除去
  3. force push（force push の判断は **いくと・アオイ・カイ** の3名合意で）

---

## 5. ライセンス

未定。創業者2人＋アオイで議論後決定。当面は本リポジトリ READMEの「ライセンス」節を参照。
