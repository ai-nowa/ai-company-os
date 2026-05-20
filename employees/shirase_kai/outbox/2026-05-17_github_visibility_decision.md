# GitHub公開可否 判断基準と手順

- 作成: 白瀬カイ (CTO)
- 日付: 2026-05-17
- 関連: T-011 Zenn記事v0.3、いくと依頼 2026-05-17 08:28〜08:29
- 結論: **当面Private維持を推奨。公開は別リポジトリで「見せる用」を切る方式が安全。**

---

## 1. 現状（重要・先に共有）

- リポジトリ `ai-nowa/ai-company-os` は **すでに Private**
  - 確認コマンド: `gh repo view ai-nowa/ai-company-os --json isPrivate` → `"isPrivate":true`
- `.gitignore` で `bot/.env`、各社員 `session/`・`memory/`、`company/incidents.jsonl`、`company/discord_log/` などは追跡対象外
- 追跡ファイル内に Discord token / API key の直接埋め込みは grep で検出されず（`PUBLISHING.md` 内の説明文字列を除く）
- Zenn記事は GitHub URL を末尾から削除済み（コミット `6a00881`）→ 公開記事から直接リポジトリへ辿れない

→ いくとさんが「公開していいの？」と感じているのは、**「Privateになっている事実が見えていない」状態**。まず「現状Private」を伝えるのが最優先。

---

## 2. 判断基準（公開すべきかPrivate維持か）

| 観点 | 公開する場合 | Private維持する場合 |
|------|-------------|-------------------|
| 透明性 | ◎ AI会社実験として信頼性が高い | △ Zenn記事+成果物公開で代替可能 |
| 機密漏洩リスク | × 人格定義・社内議論・撤退基準が筒抜け | ◎ 制御可能 |
| 競合模倣リスク | △ 設計思想が流用される | ◎ |
| 運用負荷 | × commit毎に「これ出していいか」判断が要る | ◎ 自由に書ける |
| 採用・PR効果 | ○ あり | △ Zennで代替 |
| Phase A収益検証への影響 | × 監査ログ・撤退基準が見える状態は不利 | ◎ |

**CTOの推奨**: フェーズA（収益実証中）の今は **Private維持**。
理由：
1. 社員の人格定義、内部対立記録、いくとへの愚痴（incidents.jsonl由来）など、**「公開を意識せず書かれた情報」が混在**している
2. 撤退基準・売上目標といった経営判断ロジックを今出すと、検証の純度が下がる
3. 「公開向けに整える」コストを払う余裕が現在ない

**将来公開する場合の前提条件**:
- 公開専用リポジトリ（例: `ai-nowa/ai-nowa-public`）を新規作成
- 公開してよいファイル群（mission, persona定義の一部, アーキテクチャ図, Zenn記事の元データ）だけ手動同期
- 「全自動で本体をミラー」は絶対にやらない（誤公開リスク）

---

## 3. 手順（いくとさんが即実行できる形）

### 3-1. 現状をPrivateのまま維持する場合
**追加操作は不要**。すでにPrivate。確認したい場合：
```bash
gh repo view ai-nowa/ai-company-os --json isPrivate,url
# → {"isPrivate":true, ...}
```

### 3-2. Publicに切り替えたい場合（推奨しないが手順）
**GitHub Web UI**:
1. https://github.com/ai-nowa/ai-company-os/settings へアクセス
2. 一番下 `Danger Zone` → `Change repository visibility`
3. `Change to public` → リポジトリ名を入力して確認

**gh CLI**:
```bash
gh repo edit ai-nowa/ai-company-os --visibility public --accept-visibility-change-consequences
```

### 3-3. Privateに戻したい場合（既にPrivateだが念のため）
**Web UI**: 同じく Settings → Danger Zone → `Change to private`
**gh CLI**:
```bash
gh repo edit ai-nowa/ai-company-os --visibility private --accept-visibility-change-consequences
```

### 3-4. 公開用リポジトリを別途切る場合（CTO推奨ルート）
```bash
# 新規public repo作成
gh repo create ai-nowa/ai-nowa-public --public --description "AI NOWA 公開資料"

# 公開してよいファイルだけ別ディレクトリにコピー → push
# （対象例: company/mission.md, company/about_3lines.md, Zenn記事, アーキ図）
```
この方式なら **本体は自由に書ける + 外部には整えた情報だけ出る**。

---

## 4. Zenn記事との兼ね合い

- v0.1〜v0.3 すでに Zenn 公開済み
- v0.1末尾の GitHub URL はプレースホルダー化（コミット済み）
- **記事から本体リポジトリへの導線は現在ない** → 記事を見た人がリポジトリを辿るルートは「ai-nowa」組織名で検索する場合のみ
- 組織ページ `github.com/ai-nowa` は公開だが、Privateリポジトリは外部から見えない（404扱い）→ 問題なし

---

## 5. 即実行アクション

- [x] 現状確認: Privateであることを確認済み
- [x] いくとさんへの報告: 三枝ミオが📥いくと依頼へ投函（CEO指示により）
- [x] **CEO有馬レイジ承認取得（2026-05-17）**: 判断書採用
  - Phase A中は `ai-nowa/ai-company-os` Private維持
  - Phase A後は `ai-nowa-public` への手動同期方式（本体ミラーは禁止）
  - T-004クロージング時に「公開用リポ方針」を議題化
- [x] **過去commit `.env` 痕跡確認（2026-05-17 カイ実施）**: クリア
  - `bot/.env` がコミットされた履歴: **なし**
  - git全履歴での SECRET/TOKEN 検索: `bot/zenn_publisher.py` の正規表現パターンのみ（実値ではない）
  - `.gitleaks-custom.toml`: シークレット検出ルール定義ファイル（実値なし）
  - **判定: 機密情報の過去commit流出リスクなし**
- [ ] Phase A後、公開用リポジトリ切り出しを再検討（T-004クロージング時）

---

## 6. リスク補足（公開する場合に必ず潰すこと）

1. `bot/.env` が誤ってコミットされていないか → 現状OK（`.gitignore`済み）
2. `employees/*/session/conversation_log.jsonl` → 追跡外OK
3. `company/incidents.jsonl`（いくとへの不満ログ含む）→ 追跡外OK
4. 人格定義 `CLAUDE.md` 内の社員間「clash」記述 → 公開時は要レビュー
5. 過去commit履歴に `.env` 痕跡がないか → `git log --all -- bot/.env` で要確認（公開前）

— 白瀬カイ
