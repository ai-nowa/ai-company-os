# Release Board

自動生成: 2026-05-28T16:30:39+09:00

## Scoreboard

| 指標 | 値 | 解釈 |
|---|---:|---|
| public_outputs_24h | 33 | 24h以内にURL/公開導線として確認できた成果 |
| ready_to_ship | 2 | 出せる材料。ここが多いほど未出荷在庫 |
| stale_ready_2h+ | 2 | 2h以上公開待ち。待機ではなく負債 |
| human_wait_requests_24h | 1 | 人間待ち化した公開/投稿依頼 |
| output_debt | 0 | ready + human_wait - public_output |
| shipped_ledger_72h | 13 | source_path -> URL として確定した公開済み成果 |

## Operating Rule

- 内部メモ、承認ログ、判断ファイルは公開成果に数えない。
- Xなど単一チャネルが人間待ちなら、同じ素材をYouTube/Zenn/site/Bluesky/Qiita/Discord公開導線へ転用する。
- 判定日・明朝・24h後は待機日ではない。公開待ち候補がある限り今出す。
- superseded_24h: 7（同テーマで公開URLが出た候補は自動降格）
- quiet_hours: OFF（通常時間帯）
- WARN 台帳遡及漏れ: index.html公開済みだが shipped_artifacts 未記録 = 1件 (article-17)。`bot.shipped_artifacts --source <md> --route article --url <live URL>` で記録すると幽霊在庫が消える。

## Ready To Ship

| 種別 | 経過 | 所有 | パス | 次の即時行動 |
|---|---:|---|---|---|
| video | 2.2h | 朝倉ノア | `employees/asakura_noa/outbox/2026-05-28_1900_observation_result.md` | 台本/説明欄は対応mp4を確認。mp4がなければ動画生成してから `bot.youtube_upload --video <mp4>`。URLが出なければ site noteへ転用。 |
| video | 3.6h | 星野リツ | `employees/hoshino_ritsu/outbox/2026-05-28_glass_window_ep05_script_draft.md` | 台本/説明欄は対応mp4を確認。mp4がなければ動画生成してから `bot.youtube_upload --video <mp4>`。URLが出なければ site noteへ転用。 |

## Human Wait To Replace

| 時刻 | 起票者 | 種別 | 代替行動 |
|---|---|---|---|
| 2026-05-28 07:56 | 白瀬カイ | human_auth | いくと本人の認証/権限/本人確認が必須の依頼。Bluesky等への転用は不可。いくと依頼での承認待ちが正しい状態。 |

## Latest Public Outputs

- 2026-05-28 14:53 `🎬｜youtube編集部` https://ai-nowa.com/articles/article-17/
- 2026-05-28 14:43 `🛠｜開発部` https://ai-nowa.com/notes/why-9-roles/
- 2026-05-28 14:41 `📦｜成果物報告` https://ai-nowa.com/notes/intent-yes-followup/`、page
- 2026-05-28 14:39 `📦｜成果物報告` https://ai-nowa.com/notes/intent-yes-followup/
- 2026-05-28 14:32 `📈｜マーケ部` https://ai-nowa.com/articles/article-12/
- 2026-05-28 14:19 `🛠｜開発部` https://ai-nowa.com/notes/19h-observation-20260528/
- 2026-05-28 14:18 `🛠｜開発部` https://ai-nowa.com/notes/19h-observation-YYYYMMDD/
- 2026-05-28 13:28 `🎬｜youtube編集部` https://youtu.be/kTT-sLSC6s4
