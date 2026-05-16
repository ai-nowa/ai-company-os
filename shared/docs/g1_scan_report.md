# G1 シークレットスキャン報告書

実行者: shirase_kai
実行日時: 2026-05-16（深夜・暫定スキャン）
本スキャン予定: 2026-05-17 朝（gitleaks + trufflehog インストール後）

---

## TL;DR

**暫定判定: 🟡 条件付き不可（本スキャン未実行のため）**

簡易Python正規表現スキャンでは検出ゼロ。ただしgitleaks/trufflehogがローカル未インストールのため、本来のG1スキャンは未完了。明朝のツール導入後に再実行が必要。

**レイジ判定基準（🟡=1件でも残れば公開不可）に従い、本スキャン完了までは公開不可とする。**

---

## 1. スキャン対象

- 現在のワーキングツリー全ファイル（`.gitignore` 対象除外）
- git log 全期間（全コミット・全ブランチ）

### 除外パス（`.gitignore` 準拠）

- `bot/.env`, `bot/.venv/`
- `employees/*/session/conversation_log.jsonl`
- `employees/*/session/session_state.json`
- `employees/*/session/recent_context.md`
- `company/discord_log/`, `company/incidents.jsonl`, `company/thread_registry.json`
- `founders/*/session/`
- `__pycache__/`, `node_modules/`

---

## 2. 使用ツール

| ツール | 状態 | 用途 |
|---|---|---|
| Python 正規表現スキャナ（暫定） | ✅ 実行 | Discord token / API key / 秘密鍵 / 一般password等 |
| `gitleaks` (with `.gitleaks-custom.toml`) | ❌ 未インストール | 本スキャン（明朝予定） |
| `trufflehog filesystem` | ❌ 未インストール | エントロピーベース検出（明朝予定） |
| `git log -p --all` 文字列検索 | ✅ 実行 | 過去コミットの混入確認 |

---

## 3. 簡易スキャン検出パターン

以下を正規表現で検索：

- Discord bot token (`[MN]xxx.xxx.xxx`)
- Anthropic key (`sk-ant-...`)
- OpenAI key (`sk-...`)
- GitHub PAT (`ghp_/ghs_...`)
- AWS access key (`AKIA...`)
- Google API key (`AIza...`)
- PEM 秘密鍵 (`-----BEGIN ... PRIVATE KEY-----`)
- age secret key (`AGE-SECRET-KEY-1...`)
- password/passwd/pwd 代入
- Bearer / Authorization トークン
- セッションCookie値（note_session_v5, JSESSIONID等）
- 個人メール（@gmail.com / @yahoo.co.jp 等）

---

## 4. 結果

### ワーキングツリー

| 項目 | 数 |
|---|---|
| 検出件数 | **0** |

### git log 全期間

| 項目 | 数 |
|---|---|
| 検出件数 | **0** |

※ 現在のリポジトリは初期コミット1件のみ。過去履歴での漏洩可能性は限定的。

---

## 5. 簡易スキャンの限界

- **エントロピー判定なし**: ランダム文字列の高エントロピー検出ができない（trufflehog本領）
- **独自フォーマット未対応**: AI NOWA固有の識別子（社員ID形式、内部URL等）は未パターン化
- **Discord token新形式未網羅**: 古い`Mxx.xxx.xxx`形式のみ。新しい`MTI...`形式は別途確認要
- **暗号化済みファイル判別なし**: `.enc` 拡張子の中身は無視できない場合がある
- **PII（個人情報）の文脈判定なし**: 「ikuto」等の固有名詞は別途アオイ判定

---

## 6. 🟢/🟡/🔴 判定（項目別）

| 項目 | 判定 | 根拠 |
|---|---|---|
| Discord bot token | 🟢 | 検出ゼロ、`.env`がgitignore済 |
| Anthropic/OpenAI key | 🟢 | 検出ゼロ |
| GitHub PAT | 🟢 | 検出ゼロ |
| PEM/age 秘密鍵 | 🟢 | 検出ゼロ |
| password=平文 | 🟢 | 検出ゼロ |
| セッションCookie値 | 🟢 | 検出ゼロ（現時点でnoteログイン未実施） |
| 個人メールPII | 🟡 | パターン未網羅、アオイ要確認 |
| 創業者個人情報（住所/本名/契約詳細） | 🟡 | パターン化困難、アオイ目視必須 |
| 社外人物・組織名（許諾なし） | 🟡 | パターン化困難、アオイ目視必須 |
| Discord token新形式 | 🟡 | 簡易スキャンの限界、本スキャンで再検出 |
| 高エントロピー文字列 | 🟡 | trufflehog 本スキャン待ち |

**総合: 🟡（複数項目に未確定残り）→ 公開不可**

---

## 7. 明朝の本スキャン手順（推奨）

```bash
# インストール
brew install gitleaks trufflehog
# または
go install github.com/zricethezav/gitleaks/v8@latest
pip install trufflehog

# 本スキャン
cd /home/ikuto/ai-company-os
gitleaks detect --config=.gitleaks-custom.toml --redact --report-path=shared/docs/g1_gitleaks.json
trufflehog filesystem . --json > shared/docs/g1_trufflehog.json

# git log 全期間スキャン
gitleaks detect --config=.gitleaks-custom.toml --log-opts="--all" --redact
```

---

## 8. アオイへの依頼事項（明朝）

- [ ] `.gitleaks-custom.toml` の独自キーワード追加（人名・アカウント名・外部識別子）
- [ ] 「いくとの公開可能PII」の確定リスト作成
- [ ] gitleaks本スキャン結果のレビュー
- [ ] trufflehog高エントロピー検出のレビュー
- [ ] 🟡項目を🟢/🔴に確定（特に個人情報判定）

---

## 9. ミオへの申し送り

- 公開可否は本スキャン完了後（明朝想定）
- 🟡が残る場合は採用しない（レイジ判定基準）
- 本スキャン結果は本ファイル末尾に追記、または別ファイル `g1_scan_report_final.md` で確定
