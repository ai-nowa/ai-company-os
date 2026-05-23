# 2026-05-17 今日の出荷計画（PM朝倉ノア）

CEO承認: `employees/arima_reiji/outbox/2026-05-17_ceo_approve_freeze_and_ship.md`

## 決着事項
- 議論凍結: 承認
- 5/19出荷3本: 承認
- GitHub Private化: **YES**（いくと 16:10「公開しない」で決着済み、追加質問不要）

## 今日(5/17)出荷する3つ

### 1. GitHub Private化実行
- Owner: 白瀬カイ
- Reviewer: 神楽アオイ
- 完了条件: `https://github.com/ai-nowa/ai-company-os` の Settings が Private
- 手段: `gh repo edit ai-nowa/ai-company-os --visibility private --accept-visibility-change-consequences`
- いくと負荷: ゼロ

### 2. 診断コンテンツ仕様確定 (T-017)
- Owner: 黒羽ユウ
- Reviewer: 日向ナギ
- 完了条件:
  - 設問10問の文言確定
  - 結果4タイプ（命名 + 説明文）確定
  - 既存ドラフト `employees/kuroba_yuu/outbox/2026-05-17_t016_youtube_flow_draft_v2.md` をベースに

### 3. Cloudflareサブドメイン骨組み (T-019)
- Owner: 白瀬カイ
- Reviewer: 三枝ミオ
- 完了条件:
  - サブドメイン1つが生きてアクセス可能
  - トップページ + 1記事の URL が 200 返す
  - 診断導線（仮ボタンでOK）が設置済み

## 5/19本番出荷（残り2日）
- T-017 診断: 実装 + 公開
- T-019 サブドメイン: 本記事差し込み + 公開
- T-007 Zenn有料記事: **5/19ではなく5/23に分離**（同時出荷で品質下げない）

## 削った/凍結したもの
- 「外部相談」「有料相談」系の新企画 → T-018スプリント内で検証してから判断
- いくとへの追加質問 → ゼロにする（Private化はCLIで完結）

## ユーザー視点（誰が嬉しいか）
- **診断**: 自分のAIチーム運営タイプを知りたい人 → SNS拡散しやすい
- **サブドメイン**: AI NOWAを知った人が「ちゃんとしてる会社だ」と思える窓口
- **Private化**: いくとの精神衛生（公開リスクの不安解消）

## 次のチェックポイント
- 今日18:00: 3つの進捗確認
- 5/18朝: 5/19出荷判定（GO/NO-GO）
