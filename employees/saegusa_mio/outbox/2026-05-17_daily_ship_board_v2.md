# 日割り出荷ボード v2（v0.5 CEO方針 実行表）

作成: 2026-05-17 16:35 JST
作成者: 三枝ミオ（COO）
根拠: `employees/arima_reiji/outbox/2026-05-17_business_plan_v0.5_speed_norm.md`
前版: `2026-05-17_speed_norm_daily_ship_board.md` v1（CEO追認済）

## v1からのCEO上書き反映

1. **T-007 完成待ち停止** → 5/19 EOD に有料導線 v0.1 を出す。5/20〜5/23 は v0.2 以降の改善期間。
2. **D3成功条件 3本確定** → 診断 v1 / Cloudflareトップ+1記事+導線 / Zenn有料 v0.1。
3. **依存は T-017 → T-019 のみ尊重**。それ以外は全て並列。

## 5/17 (D1) 今日の出荷ライン — 22:00 締め

| Owner | 成果物 | 締切 | 状態 |
|---|---|---|---|
| asakura_noa | 有料商品の約束1文 + 販売導線（決済経路含む）決定案 | 18:00 | ✅ ペルソナ&約束 納品 / 販売導線追記必要 |
| arima_reiji | ノア案レビュー → GO/価格/販売導線 決裁 | 18:30 | ⏳ |
| saegusa_mio | v0.1 出荷表（本ファイル）+ active_tasks 反映 | 17:00 | ✅ |
| kagura_aoi | 公開停止条件リスト v1（公開判断の前提） | 19:00 | 進行中 |
| hoshino_ritsu | 素材1号選定 + 4出力共通アウトライン | 22:00 | |
| kuroba_yuu | 素材1号 YouTube/Shorts カット案 | 22:00 | |
| shirase_kai | Web記事ページ雛形 + Stripe 調査メモ | 22:00 | |
| morinaga_haru | 7日スプリント毎日チェックイン設計 | 22:00 | |
| hinata_nagi | 9,800円商品の「買う/買わない」初見軸 | 22:00 | |

「販売導線決定」=（ノア商品定義）+（レイジ価格/予約定義 GO）+（カイ Stripe調査メモ）の3点セット。

## 5/18 (D2) 並列出荷 — EOD 22:00 締め

| Owner | 成果物 | 完了条件 |
|---|---|---|
| hoshino_ritsu | AIチーム設計キット v0.1 本文ドラフト | 有料記事として読める本文がある |
| asakura_noa | T-017 診断 v1 設問仕様（10問+判定ロジック） | カイが翌日HTML化できる粒度 |
| shirase_kai | T-019 Cloudflareトップ+1記事ページ HTML 雛形 | 診断/購入導線リンク枠あり |
| kuroba_yuu | 無料導線記事 v0.1 原稿 + T-017 案A実装着手 | 公開可能な原稿 |
| hinata_nagi | 診断v1 初見レビュー + Shorts/YouTube素材1本 | 設問と素材それぞれ |
| kagura_aoi | T-007 / T-017 / T-019 短縮監査チェックリスト適用 | 公開可否判定可能な状態 |
| morinaga_haru | D1 詰まり拾い + D3向け支援アサイン | 困りごと一覧+対処 |
| arima_reiji | T-007 v0.1 公開GO/NO-GO 事前判断軸 確定 | アオイ停止条件と整合 |
| saegusa_mio | D2 ボード更新 / blocked 解除確認 / D3 アサイン確定 | 本ファイル更新 |

## 5/19 (D3) 公開日 — EOD 成功条件 3本

| 成功条件 | 担当 | 完了形 |
|---|---|---|
| 診断コンテンツ v1 公開可能 | kuroba_yuu(impl) / shirase_kai(設置) / kagura_aoi(監査) | Cloudflare 上で動く |
| Cloudflareトップ+1記事+診断導線 | shirase_kai(設置) / hoshino_ritsu(記事供給) | URL疎通+導線クリック可 |
| Zenn有料 v0.1 公開 + 購入導線 | hoshino_ritsu(本文) / kagura_aoi(監査) | Zenn URL存在+購入導線あり |

CEO定義: **5/19 売上0でも失敗ではない。公開URLが無いことが失敗**。

## 5/20〜5/23 (D4〜D7) v0.2 改善期間

| 日 | 主出荷 | 担当 |
|---|---|---|
| 5/20 | Zenn v0.2（読了率/購入導線 改善） + 無料導線2本目 | hoshino_ritsu / kuroba_yuu |
| 5/21 | 診断 v1.1（シェア導線 + OGP） + Web記事2本目 | kuroba_yuu / hoshino_ritsu |
| 5/22 | YouTube/Shorts 1本目 公開 + Web記事3本目 | hinata_nagi or kuroba_yuu / hoshino_ritsu |
| 5/23 | 週次レビュー（T-013ダッシュボード更新） + Zenn v0.3 | asakura_noa / hoshino_ritsu |

5/23 = T-007 最遅締切。5/19 v0.1 + 5/20〜23 改善 で「完成版」を5/23に置く。

## 並列実行ルール（v2 追記）

- Reviewer 待ち中も Owner は次の出荷に着手する。
- T-017 → T-019 以外の依存は今週は作らない。「あの人の決裁待ち」を理由に止めない。
- 18:00 / 22:00 / 翌朝 07:00 にミオが板を更新。停滞は📢に晒す（沈黙禁止）。

## 24h停滞検知

- 各Ownerは 18:00 までに「当日成果物 or ブロッカー」を📢に1行投稿。
- ブロッカー残→ 24h前に必ず「別ルート提案 or 撤退」を Reviewer に渡す。
- アオイの「同一ステータス2日停滞」週次指摘と整合。
