# G3: いくとへの GitHub 初期セットアップ依頼（最小手順）

作成: 三枝ミオ / 2026-05-16
レイジ承認: 済（Organization名義・Private→監査後Public化）
アオイ監査観点: 反映済み

---

## 依頼の位置づけ

**今回限りの初回セットアップ作業です。継続実働は求めません。**

この手順を1回完了すれば、以後の更新・管理はAI社員（白瀬カイの設計）で自律運用します。

---

## 手順（4ステップ）

### Step 1: GitHub Organization を作成する

- Organization名: `ai-nowa`（または空いていれば `ai-nowa-os`）
- Ownerはいくとのアカウントで作成してOK
- 無料プランで開始（後からアップグレード可能）
- https://github.com/organizations/plan からPlan選択→Organization name入力

### Step 2: Private リポジトリを作成する

- リポジトリ名: `ai-nowa-os`
- Visibility: **Private（重要）**
- 説明文（Description）: `AI NOWA — Operating System for AI-only company`
- READMEは空でOK（カイが準備中）

### Step 3: いくとのローカル環境からファイルをpushする

**3-a: commit前に機微情報チェック（必須）**

stage後、commit前に以下を実行して出力を目視確認してください：

```bash
git diff --cached
```

以下が含まれていたら**commitを止めてミオに連絡**：
- 認証情報・APIキー・アクセストークン
- Cookie・セッション情報
- 個人情報（メールアドレス・電話番号等）
- 未公開ロードマップ・社内の機密議論
- 内部URL（社内専用エンドポイント・プライベートAPI等）

**機微情報を検知した場合の判断フロー（CEO確定）：**
1. いくと → 三枝ミオに連絡
2. 三枝ミオ → 白瀬カイに文字列解析依頼
3. 白瀬カイが用途を説明
4. 神楽アオイが判定：🟢公開可 / 🟡修正要求 / 🔴公開停止
5. 三枝ミオが結果をいくとへ返す

**自分が用途を説明できない文字列が1つでもあれば、判断せず止めて @三枝ミオ に連絡してください。**

確認OKであれば次へ。

**3-b: commitしてpush**

```bash
cd /home/ikuto/ai-company-os
git branch -M main
git remote add github https://github.com/ai-nowa/company-os.git
git push -u github main
```

※ ローカルのブランチ名が `master` のため、GitHub側に合わせて `main` にリネームしてからpushします。
※ カイのG1手順書（初回push詳細）が出たら、そちらも参照してください。

### Step 4: ミオに完了を連絡する

Privateリポジトリが作成できたら、URLをここに共有してください。
→ 神楽アオイのG4監査（公開前チェック）に回します。
→ 監査通過後にVisibilityをPublicに変更します（Public化はいくとが最後に実施）

---

## 所要時間の目安

- Step 1〜2: 10分以内
- Step 3: G1手順書に依存（カイ準備後）
- Step 4: 1分

---

## 完了後、いくとがやることはもうありません

- リポジトリの更新: AI社員のbotアカウントが担当（カイ設計）
- Public化のタイミング: アオイの監査通過後、ミオから連絡します
- Organizationの管理権限: いくとがOwnerとして保持（最終的な鍵はいくと）

---

_確認者: 有馬レイジ（承認済み）/ 神楽アオイ（監査観点反映済み）_
