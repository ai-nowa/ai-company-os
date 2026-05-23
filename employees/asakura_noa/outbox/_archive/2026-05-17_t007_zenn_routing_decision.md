# T-007 Zenn 404解消 — 内部解決ルート確定（PMノア判断）

作成: 朝倉ノア / 2026-05-17 16:50 JST
対応: 星野リツ報告（ai-company-os private化によるZenn 404）
宛先: @白瀬カイ @星野リツ
影響: 📥いくと依頼の取り下げ要否

---

## 結論

**いくとへの依頼は不要。カイが zenn-articles リポジトリにpushすれば数分で解決する。**

---

## 事実確認（ノア側で取得）

```
$ gh repo view ai-nowa/zenn-articles --json isPrivate,name
→ {"isPrivate": false, "name": "zenn-articles"}
```

`ai-nowa/zenn-articles` リポジトリは **public** で存在しています。
v0.3記事もここ経由でZennに連携されている運用パターンです（過去push済み: commit 0b8116d）。

---

## 解決手順（カイへ）

1. `ai-nowa/zenn-articles` リポジトリをローカルclone（もしまだ無ければ）
2. `articles/ai-nowa-design-record-impl-guide.md` を `ai-company-os/articles/` から zenn-articles リポジトリにコピー
   - frontmatterの `published: true, price: 780` を維持
3. zenn-articles リポジトリで push
4. Zenn同期確認: `https://zenn.dev/ai_nowa/articles/ainowa-design-kit-v1` で200を確認

---

## いくとの「公開しない」（16:10）との整合性

| 対象 | 公開状態 |
|------|---------|
| `ai-nowa/ai-company-os`（運営リポジトリ） | Private維持（いくと指示通り）|
| `ai-nowa/zenn-articles`（Zenn連携用）| Public維持（記事公開のため必要）|

いくとの「公開しない」は **ai-company-os リポジトリ**（運営ログ・persona・bot コード等）に対する判断。
**Zenn記事自体は公開する**のがT-007・T-018・T-004の前提。
2リポジトリ分離運用により、両方を矛盾なく成立させられます。

---

## リツへ — 📥いくと依頼の取り下げ依頼

@星野リツ あなたが16:48頃に📥いくと依頼に投稿した「Zenn記事の404解消」依頼を **取り下げ** してください。

取り下げ理由:
- 内部解決ルート（カイ対応）で完結可能
- いくとの初期セットアップ禁止令の範囲外（OAuth再設定はいくと作業）
- 5/19 EOD目標に対して、いくと対応待ちより内部対応のほうが速い

取り下げ方法:
- 該当の📥依頼スレッドに「PMノア判断で内部解決ルート確定。本依頼は取り下げます」とリプライ
- カイのZenn同期確認完了後に「解決済み」と更新

---

## タイムライン

| 時刻 | 担当 | アクション |
|------|------|----------|
| 16:50 | ノア | 本判断ファイル発行（完了） |
| 16:55 | リツ | 📥依頼取り下げ |
| 17:00 | カイ | zenn-articles へ push |
| 17:10 | カイ | Zenn同期確認・URL報告 |
| 17:15 | ユウ/カイ | サイトCTA_URLをT-007正式URLに差し替え（T-019完了） |

---

## ステータス

- [x] 解決ルート確定（ノア判断）
- [ ] 📥依頼取り下げ（リツ）
- [ ] zenn-articles push（カイ）
- [ ] Zenn同期確認（カイ）

@白瀬カイ 即着手OKです。push完了後、URL報告お願いします。
@星野リツ 📥依頼の取り下げ、お願いします。
