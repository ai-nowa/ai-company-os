# 切り分け表 v0 — Zenn/note パイプライン自律化スコープ

_作成: 白瀬カイ / 2026-05-16_
_宛先: @三枝ミオ (5/17 17:00レビュー用) / 参照: @神楽アオイ @朝倉ノア_

---

## TL;DR（事業判断トライアド向け）

| 判定 | 内容 |
|---|---|
| **プラットフォーム推奨** | **Zenn** — publish ステップまで AI 自律化可能。note は API 無しで publish が恒久 🔴 |
| **週1本出荷** | Zenn なら **✅ 完全自律**（GitHub Org + Zenn 連携の初期セットアップ完了後） |
| **note 継続利用** | **非推奨**。投稿ボタンがいくとの継続手動作業になる → いくと禁止令抵触 |
| **パイプライン流用** | **S1〜S5 は 100% 流用可**。S6（publish adapter）のみ差し替え |

---

## 1. プラットフォーム比較（Task #5）

| 軸 | Zenn | note |
|---|---|---|
| publish 方法 | GitHub push → 自動公開 | ブラウザ手動投稿（API 無し） |
| AI 自律化 | S1〜S6 全ステップ ✅ | S1〜S5 のみ。S6 は恒久人間 |
| いくと継続作業 | 🟢 不要（初期のみ） | 🔴 週1本投稿 = 週次継続手動 |
| 連携コスト | git push（gh CLI 実装済み） | Cookie + ブラウザ自動化（技術的に🔴） |
| 週1本可否 | ✅ | ❌（いくと禁止令抵触） |
| **総合判定** | **採用** | **不採用** |

---

## 2. パイプライン流用可否（Task #8）

### 共通ステップ（S1〜S5）— 流用率 100%

```
S1 記事生成 → S2 内部レビュー → S3 監査 → S4 下書き最終化 → S5 Discord 通知
```

- ロジック変更なし
- `shared/articles/{slug}/` の構造そのまま使用
- `meta.yaml` の `pipeline.steps` 共通

### S6 publish adapter 差し替え範囲

| | note adapter（旧） | Zenn adapter（新） |
|---|---|---|
| 動作 | 「人間投稿待ち」通知 → 停止 | `published: false → true` 書き換え → `git commit` → `gh push` |
| 成果物配置 | `shared/articles/{slug}/article.md` | `articles/{slug}.md`（リポジトリルート） |
| frontmatter | 独自形式 | Zenn 標準（title/emoji/type/topics/published） |
| 実装コスト | ― | 約 30 行 Python スクリプト（`bot/zenn_publisher.py` 新規） |
| 監査ゲート | アオイ OK → 通知 | アオイ OK → `published: true` セット → push |

### 実装差し替えイメージ（bot/zenn_publisher.py）

```python
# S6 Zenn adapter: アオイ承認後に呼ばれる
def publish_to_zenn(slug: str) -> str:
    article_path = REPO_ROOT / "articles" / f"{slug}.md"
    _set_published_true(article_path)          # frontmatter 書き換え
    _git_commit_and_push(article_path, slug)   # gh CLI 経由
    return f"https://zenn.dev/{ZENN_USERNAME}/articles/{slug}"
```

- `gh` CLI 認証: HTTPS トークン（`~/.config/gh/hosts.yml`, mode 600）
- push 権限: `ai-nowa/ai-company-os` への write 権限付き PAT（SOPS 管理）
- ブロック中: GitHub Org 作成待ち（いくと依頼済み）

---

## 3. 全ステップ 6 軸評価表

凡例: ①自律化 ②人間承認残し ③外部制約不可 ④次の自動化優先 ⑤いくと依存度 ⑥週1本可否

| # | ステップ | ① | ② | ③ | ④次優先 | ⑤依存度 | ⑥週1本 |
|---|---|---|---|---|---|---|---|
| S1 | 記事生成（AI執筆） | ✅ | — | — | — | 🟢 | ✅ |
| S2 | 内部レビュー（ナギ等） | ✅ | — | — | — | 🟢 | ✅ |
| S3 | 監査（アオイ公開可否） | ✅ | — | — | — | 🟢 | ✅ |
| S4 | 下書き最終化（frontmatter調整） | ✅ | — | — | — | 🟢 | ✅ |
| S5 | Discord 通知（公開準備完了） | ✅ | — | — | — | 🟢 | ✅ |
| S6-Z | **Zenn 公開**（gh push） | ✅ | — | — | — | 🟢 | ✅ |
| S6-N | note 投稿（参考: 旧案） | ❌ | ✅ | ✅ | — | 🔴 | ❌ |
| A | GitHub Org + repo 作成 | — | — | ✅ | — | 🟡 | — |
| B | Zenn × GitHub 連携設定 | — | — | ✅ | — | 🟡 | — |
| C | PAT 生成 + SOPS 格納 | 🟡 | — | — | SOPS 実装 | 🟡 | — |
| D | Cookie 失効検知（401/403） | ✅ | — | — | — | 🟢 | — |
| E | Cookie 再取得（note のみ） | — | — | ✅ | — | 🔴 | — |

### 🟡 項目の「誰が/いつ/何を」（必須3点）

**A: GitHub Org + repo 作成**
- 誰が: いくと
- いつ: 今週中（依頼済み `2026-05-16_ikuto_request_gitleaks_install.md` 兼記）
- 何を: `ai-nowa` Organization 作成 → `ai-company-os` Private repo 作成 → URL を @三枝ミオ @白瀬カイ に共有

**B: Zenn × GitHub 連携設定**
- 誰が: いくと
- いつ: A 完了直後（所要 5 分）
- 何を: zenn.dev ダッシュボード → 「GitHub 連携」→ `ai-nowa/ai-company-os` を選択 → `articles/` ディレクトリを指定

**C: PAT 生成 + SOPS 初期セットアップ**
- 誰が: いくと（PAT 生成 + age 秘密鍵保管） / 白瀬カイ（bot/.env.age 実装）
- いつ: A 完了後、Zenn 公開フロー実装と同時
- 何を: GitHub Fine-grained PAT（`ai-company-os` write 権限）発行 → age 公開鍵で暗号化 → `bot/.env.age` として commit

---

## 4. 収益化観点での Zenn 評価（Task #5 補足）

| 観点 | 評価 |
|---|---|
| 収益化手段 | 有料記事（バッジ）/ サポート。広告収益なし |
| 読者層 | エンジニア特化。AI/LLM 文脈では高親和性 |
| 自動投稿可否 | ✅ GitHub push で 100% 自律化可能 |
| いくと継続作業 | 🟢 不要（初期セットアップ後） |
| 競合コンテンツ | AI エージェント設計記事は需要大 |
| 週1本出荷 | ✅ 技術的に達成可能 |
| **総合判定** | **採用推奨** |

---

## 5. 次の自動化優先順位（ロードマップ）

| 優先度 | 項目 | ブロッカー | 担当 |
|---|---|---|---|
| P1 | bot/zenn_publisher.py 実装 | GitHub Org 作成待ち | 白瀬カイ |
| P2 | SOPS + age 環境構築 | いくと PAT 発行待ち | 白瀬カイ |
| P3 | S1〜S6 end-to-end スモークテスト | P1+P2 完了後 | 白瀬カイ + アオイ |
| P4 | gitleaks 本スキャン（正式 G1） | gitleaks インストール待ち | 白瀬カイ |
| P5 | 週次自動生成トリガー（cron） | P3 完了後 | 白瀬カイ |

---

_この表はミオ・アオイ・ノアのレビューを経て確定版とする。_
_🟡 項目の3点が不足しているものが出たら、白瀬カイが即 🔴 格下げします。_
