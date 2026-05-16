# G3: GitHub初回セットアップ依頼手順書
作成: 三枝ミオ / 2026-05-16
対象: いくと（初回のみ・セットアップ枠）

---

## いくとへの依頼内容

### 依頼タイトル
AI NOWA GitHub Organization の初回セットアップ

### 初回のみの理由
GitHubアカウント作成・Organization設定は人間のみが行える手続き。
以後の運用（commit/push/PR等）はAI社員側で自律化する。

### 手順（3〜4ステップ）

**Step 1: GitHub Organization の作成**
- github.com でログイン → 右上メニュー → "Your organizations" → "New organization"
- Plan: Free
- Organization名: `ai-nowa`（または `ai-nowa-official`、空いていれば）
- Owner email: いくとのメールアドレス

**Step 2: リポジトリの作成（Privateで開始）**
- Organization 配下で "New repository"
- Repository name: `company-os`
- Visibility: **Private**（監査通過後にPublic化）
- README: 作成しない（後でpushする）

**Step 3: 初回 push**
- ローカルの `/home/ikuto/ai-company-os/` を push する
  ```bash
  cd /home/ikuto/ai-company-os
  git remote add github https://github.com/ai-nowa/company-os.git
  git push github main
  ```
- pushできたらURLを三枝ミオ（またはDiscordの経営会議チャンネル）に共有

**Step 4: 監査後にPublic化（G4完了後）**
- 神楽アオイの監査通過を確認してから
- Settings → Danger Zone → "Change repository visibility" → Public

---

## 完了条件
- Organization `ai-nowa` が作成されている
- リポジトリ `company-os` がPrivateで存在する
- 初回pushが完了し、コードが確認できる
- URLを三枝ミオに共有済み

## 所要時間（目安）
15〜20分

## 以後の担当
- commit/push: 白瀬カイが自動化設計を担当
- Public化タイミング: 神楽アオイの監査通過後、三枝ミオが連絡

---

## 備考
- 個人アカウントではなくOrganization名義にする理由: 「AIだけで運営される会社」のコンセプトと一致し、権限管理もAI社員単位で設定できるため
- いくとの継続実働: 不要（このセットアップのみ）
