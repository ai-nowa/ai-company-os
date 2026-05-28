# Release Board

自動生成: 2026-05-28T10:50:25+09:00

## Scoreboard

| 指標 | 値 | 解釈 |
|---|---:|---|
| public_outputs_24h | 27 | 24h以内にURL/公開導線として確認できた成果 |
| ready_to_ship | 0 | 出せる材料。ここが多いほど未出荷在庫 |
| stale_ready_2h+ | 0 | 2h以上公開待ち。待機ではなく負債 |
| human_wait_requests_24h | 1 | 人間待ち化した公開/投稿依頼 |
| output_debt | 0 | ready + human_wait - public_output |
| shipped_ledger_72h | 15 | source_path -> URL として確定した公開済み成果 |

## Operating Rule

- 内部メモ、承認ログ、判断ファイルは公開成果に数えない。
- Xなど単一チャネルが人間待ちなら、同じ素材をYouTube/Zenn/site/Bluesky/Qiita/Discord公開導線へ転用する。
- 判定日・明朝・24h後は待機日ではない。公開待ち候補がある限り今出す。
- superseded_24h: 20（同テーマで公開URLが出た候補は自動降格）
- quiet_hours: OFF（通常時間帯）

## Ready To Ship

- なし

## Human Wait To Replace

| 時刻 | 起票者 | 種別 | 代替行動 |
|---|---|---|---|
| 2026-05-28 07:56 | 白瀬カイ | human_auth | いくと本人の認証/権限/本人確認が必須の依頼。Bluesky等への転用は不可。いくと依頼での承認待ちが正しい状態。 |

## Latest Public Outputs

- 2026-05-28 08:26 `🛠｜開発部` https://youtu.be/e2ZNNfTZ2nU
- 2026-05-28 08:26 `company/shipped_artifacts.jsonl` https://youtu.be/kTT-sLSC6s4
- 2026-05-28 08:24 `🛠｜開発部` https://ai-nowa.com/r/ep03-about
- 2026-05-28 08:21 `🛠｜開発部` https://ai-nowa.com/r/ep01-about
- 2026-05-28 05:52 `🎯｜経営会議` https://youtu.be/erZ1FrWRE8E
- 2026-05-28 05:21 `🎯｜経営会議` https://ai-nowa.com/notes/mode-density/
- 2026-05-28 04:40 `🎯｜経営会議` https://bsky.app/profile/did:plc:oyjykf2iizpj5hzq4t5fpx6h/post/3mmu775qx5n2o
- 2026-05-28 04:00 `🎯｜経営会議` https://ai-nowa.com/notes/starter-kit-openbox/?utm_source=site&utm_medium=internal_note&utm_campaign=t004_openbox_reach
