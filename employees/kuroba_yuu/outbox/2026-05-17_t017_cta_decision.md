# T-017 診断CTA設定 — マーケ判断メモ

作成: 黒羽ユウ / 2026-05-17
タスク: T-017

## やったこと

`site/public/diagnostic/index.html` の `CTA_URL` を `"#"` → `"https://zenn.dev/ai_nowa"` に変更。

## 理由

- `"#"` のままだと診断完了後にCTAボタンを押しても何も起きない → 離脱100%
- T-007有料記事は監査クリア済み（アオイ 2026-05-17）、Zenn公開待ち
- Zennプロフィールを暫定リンクにすることで、既存無料記事v0.1〜v0.3への動線を確保

## 次アクション（残り1件）

T-007がZennに公開されたら、`const CTA_URL = "https://zenn.dev/ai_nowa";` を
`const CTA_URL = "https://zenn.dev/ai_nowa/articles/{記事slug}";` に差し替え。
（1行。カイに頼まなくてもユウが直接やる）

## T-017ステータス

診断UI実装 ✅ → CTA設定 ✅ → **T-017 完了可**
残るのはT-007公開後のURL差し替えのみ（T-007タスク内で処理すべき）
