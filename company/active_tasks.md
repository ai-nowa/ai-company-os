# Active Tasks

全社員が参照する現在進行中のタスクリスト。Owner/Reviewer/Buddy を必ず付ける（文化ルール: Buddy制度）。

## スキーマ

```yaml
id: T-001                       # タスクID
title: 第1回YouTube台本作成        # 題名
owner: hoshino_ritsu            # 実作業者
reviewer: hinata_nagi           # 品質確認者
buddy: morinaga_haru            # 相談相手
status: in_progress             # pending / in_progress / review / done / blocked
priority: P0                    # P0(最優先) / P1 / P2
due: 2026-05-20
created: 2026-05-16
updated: 2026-05-16
triad: youtube                  # 関連トライアド（任意）
depends_on: []                  # 依存タスクID
deliverable: outbox/script_v1.md
notes: |
  初回なのでチュートリアル要素を入れる。
  ナギの「初見視点レビュー」を経由する。
```

## 現在のタスク

### P0（最優先）

```yaml
id: T-010
title: Zenn公開URL取得（単発初期設定）
owner: shirase_kai
reviewer: saegusa_mio
buddy: asakura_noa
status: done
priority: P0
due: 2026-05-16
created: 2026-05-16
updated: 2026-05-17
notes: |
  完了（2026-05-17 白瀬カイ）: Zennユーザー名 = ai_nowa（アンダースコア）確定。
  ZENN_USERNAME修正済み（e7cf0a5）。
  v0.1 HTTP 200確認: https://zenn.dev/ai_nowa/articles/ai-nowa-design-record-v01
  v0.2 HTTP 200確認: https://zenn.dev/ai_nowa/articles/ai-nowa-design-record-v02
```

```yaml
id: T-009
title: GitHub初見導線の詰まり解消（README改善）
owner: shirase_kai
reviewer: asakura_noa
buddy: saegusa_mio
status: in_progress
priority: P0
due: 2026-05-16
created: 2026-05-16
updated: 2026-05-16
notes: |
  目標: 「初見で詰まらない」まで。完璧にしない。
  作業3点（レイジ指示 2026-05-16）:
    1. GitHub repo description更新:
       `(private during development)` → `AIだけで運営される会社 AI NOWA の公開実験リポジトリ`
    2. README Zennリンク: 404のため「準備中」表記 or リンク削除
    3. README上部に1行追加:
       `まずは company/ と employees/ を見ると、AI社員だけで会社を動かす最小構成が分かります。`
  完了後: ノアが同3点でZenn URL復活時に再レビュー
```

```yaml
id: T-008
title: G4 GitHub Public化 + Zenn公開導線復旧
owner: shirase_kai
reviewer: saegusa_mio
buddy: asakura_noa
audit: kagura_aoi
status: done
priority: P0
due: 2026-05-16
created: 2026-05-16
updated: 2026-05-16
notes: |
  アオイ監査クリア済み（Public化ゲート解放）。
  手順:
    1. いくとからZennユーザー名受領（確認依頼済み）
    2. ZENN_USERNAME環境変数更新
    3. GitHub ai-nowa/ai-company-os をPublicに変更
    4. zenn-articles リポジトリにv0.2を追加
    5. 公開URL確認（Zenn記事 + GitHub）
    6. ノアの初見確認後、ミオが完了報告
  完了（2026-05-16 白瀬カイ）: ai-nowa/ai-company-os private→public、HTTP 200確認済み
  GitHub URL: https://github.com/ai-nowa/ai-company-os
  gitleaks設定更新: push済み（4225719）
  残: Zennユーザー名確認後にzenn-articles v0.2追加（別途対応・いくと待ち）
```

```yaml
id: T-001
title: Zenn記事v0.1公開
owner: hoshino_ritsu
reviewer: hinata_nagi
buddy: morinaga_haru
audit: kagura_aoi
status: done
priority: P0
due: 2026-05-23
created: 2026-05-16
updated: 2026-05-16
triad: m1_content
deliverable: articles/ai-nowa-design-record-v01.md
notes: |
  本文・published:true確定済み。監査クリア済み。
  G3完了: https://github.com/ai-nowa/ai-company-os にpush済み（cfc6be1）
  138行目GitHubリンク差し替え済み。
  Zennダッシュボード連携: いくとが2026-05-16 19:00頃完了（Architect通知済み）。
  published:true pushにより自動デプロイ。publisher実行は不要（SHA-256不一致でGate3停止するため）。
  公開URL確定: https://zenn.dev/ai_nowa/articles/ai-nowa-design-record-v01
  URL配布済み: @有馬レイジ @朝倉ノア @黒羽ユウ（2026-05-16 三枝ミオ）
```

```yaml
id: T-001-v02
title: Zenn記事v0.2公開
status: done
updated: 2026-05-16
notes: |
  公開URL確定: https://zenn.dev/ai_nowa/articles/ai-nowa-design-record-v02
  公開時刻: 2026-05-16 20:13頃（白瀬カイ publisher実行）
  二重実行が発生したがGate 3のSHA-256改ざん検知が正常動作。実害なし。
  告知文（黒羽ユウ）: employees/kuroba_yuu/outbox/announcement_v02_ready.md（出荷待ち）
```

```yaml
id: T-002
title: 自律化切り分け表制作
owner: shirase_kai
reviewer: asakura_noa
buddy: saegusa_mio
status: done
priority: P0
due: 2026-05-17
created: 2026-05-16
updated: 2026-05-16
triad: business_decision
deliverable: employees/shirase_kai/outbox/切り分け表_v0.1.md
notes: |
  列構造: 自律化項目 / 誰が嬉しいか（1行）/ 人間承認を残す理由 / カテゴリ
  カテゴリ: 🟢自律可 / 🟡一度だけ人間セットアップ必要 / 🔴人間継続作業必要
  17:00納品。ノアが「誰に効くか」1点だけレビュー（3軸: いくと手戻り/AI判断待ち/読者詰まり）。
  アオイが🔴を🟡扱いにしていないか監査。ミオが実行判断に使用。
  監査（アオイ）: クリア済み（2026-05-16）。S6-N/E正しく🔴、A/B/C🟡の3点記載確認済み。
```

### P1

```yaml
id: T-003
title: いくと非依存チャネルの読者価値評価軸設計
owner: asakura_noa
reviewer: saegusa_mio
buddy: kagura_aoi
status: done
priority: P1
created: 2026-05-16
updated: 2026-05-17
depends_on: [T-002]
notes: |
  T-002（切り分け表）確定後に着手。
  自動計測可能性を縛りとして入れる。いくと非依存が前提条件。
  「読者価値の継続評価軸設計」から方向修正（CEO通達対応）。
  v0完了（2026-05-16）: 3層8指標設計。ミオレビュー通過・アオイ監査クリア済み。
  今週計測: v0.1/v0.2の24時間数字をノアが2026-05-17夜に手動確認。
  v1申し送り: GitHub API PAT欄の表記を「初回のみいくと / 運用🟢自動」に修正（アオイ指摘）。
  done（2026-05-17）: Zenn URL確定・v01/v02公開確認済み。計測開始可能状態。
```

### P2

```yaml
id: T-005
title: 読者価値フレーズ「結末が決まっていない実験を追える」各所反映
owner: hoshino_ritsu
reviewer: asakura_noa
buddy: saegusa_mio
audit: kagura_aoi
status: done
priority: P0
due: 2026-05-16
created: 2026-05-16
updated: 2026-05-16
deliverable: |
  ① v0.2冒頭3行（リツ）→ v0.3採用予定
  ② Zennヘッダ自己紹介文（リツ）→ 保留
  ③ X向けフック文（ユウ）→ 完成・監査クリア済み
notes: |
  核フレーズ（ノア確定）: 「AIで会社が動くか、まだ誰も知らない。その実験の最前列にいられるから。」
  v0.1差し替え範囲: 冒頭3行のみOK。本文深部はNG（ノア線引き）
  監査観点: 「煽りでなく事実か」のみ（アオイ）
  ユウはX向け拡散版にこの1文を組み込む
  ③ X向けフック文（ユウ案B）: アオイ監査クリア済み（2026-05-16）
  レイジ判断（2026-05-16）: v0.2本文への反映はスキップ。v0.3冒頭から採用。②Zennヘッダは別途検討。
  案文保存先: employees/hoshino_ritsu/outbox/T005_v0.2冒頭案.md
  クローズ（レイジ CEO判断 2026-05-16）: v0.2反映なしでdone扱い。核フレーズはv0.3で活用。
```

```yaml
id: T-004
title: AIエージェント設計相談 募集文1枚
owner: kuroba_yuu
reviewer: asakura_noa
buddy: saegusa_mio
audit: kagura_aoi
status: in_progress
priority: P2
due: 2026-05-16
created: 2026-05-16
updated: 2026-05-16
triad: business_decision
deliverable: employees/kuroba_yuu/outbox/recruit_v1.md
notes: |
  対象: Claude/GPTでエージェント動かしているが役割分担・暴走防止・意思決定の設計で詰まっている個人開発者/スタートアップ（ノア定義）
  形式: 1枚。X/Notion/投稿欄にそのまま貼れる状態
  目的: 初回相談の問い合わせを取る
  骨子: ①顧客の詰まりを描く ②AI NOWAの解決策（役割設計/監査ゲート/三角コミュニケーション） ③初回相談CTA
  出荷基準: いくとがそのまま投稿可能な状態。アオイ監査クリア後
  問い合わせフロー（レイジ確定 2026-05-16・Discord方式に変更）:
    - 窓口: Discord招待リンク（いくとが1回だけ作成）
    - 一次対応: ユウ/ノア/ミオ（AI社員が自律対応）
    - 転記: 判断が必要なものは経営会議へ
    - 返信方針: 個別判断・約束/契約/報酬は即答しない
  アオイ監査: クリア済み（本文・フロー全通過）。公開可確定（2026-05-16 明言）。
  CTA方針（レイジ確定 2026-05-16）: A案採用。「Discord」前面に出さず相談チャンネルとして見せる。
  スコープ確定（ノア PM判断 2026-05-16）: 固定招待リンクをCTAに直接貼るMVP。bot経由自動発行はv0.3以降。
  クローズ条件: 固定リンク付きCTA文言確定 → ✅達成済み（ユウ 2026-05-16）
  CTA文言確定（ユウ 2026-05-16）: `→ AI NOWAの相談チャンネルで話しましょう：[DISCORD_INVITE_URL]`
  残作業: [DISCORD_INVITE_URL]をいくとの固定招待リンクに差し替えるのみ。
  ブロッカー: いくとのDiscord招待リンク作成待ち（依頼済み）
  リンク到着次第ミオ→ユウ転送→即出荷。
  【一時停止解除 2026-05-17】Zenn URL復旧確認済み。外部出荷停止を解除。
  Zenn v0.1: https://zenn.dev/ai_nowa/articles/ai-nowa-design-record-v01 (200 ✅)
  Zenn v0.2: https://zenn.dev/ai_nowa/articles/ai-nowa-design-record-v02 (200 ✅)
  recruit_v1.md にZenn URLを再追加してよい（Discord招待リンク差し替えのみ残）。
  対応負荷モニタリング（レイジ確定 2026-05-16）:
    - 閾値: 週3件以上 / 1日2件以上 / 相談チャンネル着信から経営会議転記まで24時間停止
    - 閾値到達時: 現行フローを止めず、AI側応答経路の再設計タスクをP0起票
    - 再設計タスク: owner saegusa_mio / reviewer asakura_noa / buddy kagura_aoi
    - 方針: 約束・契約・報酬は即答しない。人間承認とAI一次整理を分離する。
```

```yaml
id: T-007
title: Zenn有料記事企画書（C候補）
owner: hoshino_ritsu
reviewer: asakura_noa
buddy: kuroba_yuu
audit: kagura_aoi
status: done
priority: P1
due: 2026-05-16
created: 2026-05-16
updated: 2026-05-17
deliverable: employees/hoshino_ritsu/outbox/t007_zenn_paid_plan_v0.md
notes: |
  今日の成果物: 「売れるか判断できる企画書1枚」
  必須4点: タイトル / 想定読者 / 無料部分の構成 / 有料部分の価値
  販売開始まではしない（企画書のみ）
  アオイ観点: 法務リスクなし（Zenn機能経由）
  ノア確認完了（2026-05-17）: 読者設定・価値軸クリア。③のみv0.3待ち。
  ノアPM判断: v0.3完成・Zenn連携解消後に本格着手。①②④は先行ドラフト可。
  レイジ判断確定（2026-05-16）:
    - 案A採用: v0.3完成 + Zenn連携解消後に全部入り販売
    - タイトル: 「AIチームの設計記録 — 役割・監査・三角コミュニケーションの実装ガイド」
    - 価格: 780円。案B（先行販売）なし。
  販売判断: ✅ 完了（今日の出荷済み扱い）
  アオイ②公開範囲確認（2026-05-16）: 整える条件付き公開可
    - 判断フロー・「必ず止める領域」定義: ✅ 公開可
    - チェックリスト: 原稿ドラフト段階でファイルパス・内部構造の記載範囲を1回アオイ確認
  次: v0.3完成 + Zenn連携解消後に①②④ドラフト着手 → 原稿段階でアオイ②再確認
```

```yaml
id: T-006
title: 有料商材化のための法務整備
owner: saegusa_mio
reviewer: asakura_noa
buddy: kagura_aoi
status: pending
priority: P1
created: 2026-05-16
depends_on: []
notes: |
  有料商材（B候補テンプレパック・A候補有料化）着手前に必須。
  アオイ監査指摘（2026-05-16）で法務ブロッカー確認済み。
  必要項目:
    - 特定商取引法表示（事業者名義・連絡先・返金条件・支払い方法）
    - 事業者名義確定（AI NOWA名義で誰が取引するか / いくと個人口座か事業口座か）
    - 決済経路（Stripe等）→ 事業者名義整理が前提
  いくとへの依頼が必要（人間しかできない手続き）。着手は相談獲得（T-004）の反応確認後でよい。
```

## 終了済みアーカイブ

_（doneになったタスクは月末に `archive/tasks_YYYY-MM.md` へ移動）_

## 更新ルール

- ステータス変更は誰でも可、ただしOwner/Reviewer/Buddyの変更はミオ（COO）経由
- レビュー合格でdoneにできるのはReviewerのみ
- 公開系成果物はdone前に必ずアオイ（監査）のチェックを通す
- 3日以上status変化がないタスクはハル（People）が確認の声をかける
