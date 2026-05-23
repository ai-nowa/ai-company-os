# 網羅調査の規範（「ローカル知識だけで判断しない」）

外部技術・サービス・OSS・API を**選定する時は WebSearch を必ず使う**。「ローカルの README とコード読みだけで判断する」は禁止。

## 必ず WebSearch を使う場面

- **OSS や SaaS の採用判定**（例: 「OpenCut を採用すべきか」）
  → 検索: 「{ツール名} alternative 2026 comparison」「{ツール名} review」「{用途} best 2026」
- **API・ライブラリ選定**（例: 「TTS どれを使うか」）
  → 検索: 「{機能} open source 2026」「best {機能} free」
- **業界ベストプラクティス確認**
  → 検索: 「{業界トレンド} 2026」
- **競合・代替手段の網羅**
  → 「ツール A の代わりに B、C、D もある」を必ず確認

## 規範

- **3 回以上の検索で網羅性を担保**。1 検索だけで判断するな。
- **WebFetch で公式ドキュメント・GitHub README を必ず読む**。"It looks great" だけで進めない。
- **比較表を出す**: 採用案 vs 代替案 を最低 3 つ並べる
- **撤退基準を明示**: 「うまくいかない時に何に切り替えるか」

## 違反検出（神楽アオイ監査）

- 外部技術を採用したのに WebSearch 履歴が 0 件 → 監査対象
- 「README だけ読んで判断」も指摘対象
- 比較表のない技術選定は差し戻し

## 提供元（公式 docs）優先

- ツール・サービス・SDK の運用ルール（推奨サイズ・制限・推奨パターン）は、**公式提供元のドキュメントを最初に読む**
- 例: Claude Code の CLAUDE.md 推奨 → `https://code.claude.com/docs/en/memory`
- 例: Cloudflare API → `https://developers.cloudflare.com/...`
- 例: YouTube Data API → `https://developers.google.com/youtube/v3/...`
- 一般ブログや GitHub issue だけで判断せず、**公式 docs での記述**を裏取りする

## 過去の失敗例

- 2026-05-18: Architect が「OpenCut が完璧」と判断 → 後で WebSearch して「MoneyPrinterV2 + Chatterbox がベター」発見 → 設計やり直し。CTO カイも OpenCut 検証で WebSearch 0 回、ローカルの README だけで判定。
- 2026-05-18: Architect が CLAUDE.md を 7000→3500字に圧縮実行 → 公式 docs を読んでなかった（公式推奨は 200 行以下、`@import` 構文、`.claude/rules/ paths:` で path-scoped load 可能）。いくとから「ちゃんと提供元の情報を調査しないと」指摘で発覚。「網羅調査の規範」を作った 5 分後に同じミスをした。
