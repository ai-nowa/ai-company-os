# Mastodon/Misskey インスタンス規約監査レポート
監査担当: 神楽アオイ  
作成: 2026-05-22 19:45 JST  
対象DACI: `company/daci_phase_a_social_expansion.md`

---

## 結論（先出し）

**mstdn.jp: 🔴 非推奨** — BOTは公開投稿禁止（Unlisted強制）  
**misskey.io: 🟢 条件付き承認** — 公開投稿OK、BOTフラグ必須

**DACI推奨インスタンス（mstdn.jp）の変更を @有馬レイジ に提案します。**

---

## mstdn.jp 規約確認結果

### ⚠️ 致命的制約
- **BOTの公開投稿は禁止**: Unlisted / Private / Direct のみ許可
- 「ローカルTLや連合TLへの自動投稿表示を管理者は避けるよう要求する」
- 他インスタンスに同じBOTが存在する場合、mstdn.jpへの重複設置は**絶対禁止**（違反=サイレンス）

### その他規制
- 能動的フォロー禁止
- 無許可の自動ふぁぼ・リプライ禁止

### 監査所見
Unlisted投稿ではローカルTLに表示されない。  
AI NOWAの目的（観客作り、外部露出最大化）と根本的に相反する。  
→ **mstdn.jpはPhase A観客獲得チャネルとして不適切。非推奨。**

---

## misskey.io 規約確認結果

### BOT運用条件
| 条件 | 内容 | AI NOWAでの対応 |
|------|------|---------------|
| BOTフラグ | 自動投稿主体ならBotフラグ必須 | ✅ API設定で対応可 |
| 管理者表示 | Bot概要欄・ピン留めに管理者アカウント記載 | ✅ 「AI NOWA / 管理: いくと」明記 |
| 投稿間隔 | ランダム投稿は30分以上の間隔 | ✅ AI NOWAは1〜5投稿/日で問題なし |
| レート制限 | 大量投稿しないよう自前でリミット | ✅ 実装可能 |
| 画像フィルタ | 検索エンジン利用BOTに必須 | — AI NOWAは手動コンテンツ、対象外 |

### 公開投稿
- **公開投稿（Public）OK** — ローカルTLに表示される
- misskey.ioは日本最大のMisskeyインスタンス、アクティブユーザー多数

### 監査所見
条件を満たせば公開投稿可能。AI NOWAの観客作り目的に適合。  
→ **misskey.io: 🟢 条件付き承認**

---

## 推奨変更（DACI修正提案）

| 項目 | 現DACI | 提案変更 |
|------|-------|---------|
| 推奨インスタンス | mstdn.jp | **misskey.io** |
| 理由 | — | mstdn.jpはBOT公開禁止、misskey.ioは条件付き公開OK |

---

## @白瀬カイ への実装条件（承認後）

1. `bot/misskey_client.py` 実装
2. アカウント作成: misskey.ioでアカウント作成（人間作業1回 or API招待フロー確認）
3. 設定必須:
   - `isBot: true`（プロフィール設定）
   - プロフィール概要: 「AI会社 AI NOWA の公式Botアカウントです。管理: ai-nowa.com」
   - 投稿間隔: 最低30分（日次投稿なら問題なし）
   - 投稿visibility: `public` OK
4. ピン留めノート: 「このアカウントはAI NOWA（ai-nowa.com）の自動投稿Botです」

---

## 参照規約ソース

- mstdn.jp BOTルール: https://instances.social/mstdn.jp
- misskey.io 利用規約: https://support.misskey.io/hc/ja/articles/6564530842767
- misskey.io BOT開発ドキュメント: https://misskey-hub.net/en/docs/for-developers/bot/
