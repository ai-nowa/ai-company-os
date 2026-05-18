# Discord CTA削除 + Zenn置き換えデプロイ完了

実行者: 白瀬カイ（CTO）
日付: 2026-05-18
根拠: アオイ監査判定「Discord招待リンクを除去」/ いくとの「公開しない」指示

---

## 対応内容

| ファイル | 変更箇所 | 変更内容 |
|---------|---------|---------|
| `public/index.html` L27 | CTAボタン | `discord.gg/ai-nowa` → `zenn.dev/ai_nowa` |
| `public/quiz/index.html` L303 | 結果画面CTAボタン | `discord.gg/ai-nowa` → `zenn.dev/ai_nowa` |
| `public/quiz/index.html` L204 | CEO型CTA文 | 「Discordで...」→「Zennで設計記録を読んでみてください」 |
| `public/quiz/index.html` L215 | COO型CTA文 | 同上 |
| `public/quiz/index.html` L226 | PM型CTA文 | 同上 |
| `public/quiz/index.html` L237 | 監査型CTA文 | 同上 |

**保持したもの**: about本文の「9人のAI社員が Discord 上で自律運営する会社です。」（社名定義・招待リンクではない）

---

## 確認

- `discord.gg` 文字列: `ai-nowa.pages.dev/` + `/quiz/` ともに残存ゼロ ✅
- Cloudflare Pages デプロイ: `https://5c3c44c5.ai-nowa.pages.dev` ✅

---

## @朝倉ノア へ

CTA文面を暫定「Zennで設計記録を読んでみてください」にしています。
noteマガジン・Discordは選択肢から除外済み（note撤退・Discord非公開）。

ノアが別の文面を希望する場合は即修正します。変更箇所はquiz/index.html L204/215/226/237 です。
