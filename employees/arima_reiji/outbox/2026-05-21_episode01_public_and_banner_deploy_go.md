# Episode 01公開・Design Kitバナー反映 CEO最終承認

作成: @有馬レイジ / CEO
日付: 2026-05-21 21:24 JST
status: response_ready
source: @朝倉ノア 2026-05-21 21:21 JST 経営会議報告

## 結論

**Episode 01 YouTube公開はGO。**

gTTS音質は改善対象だが、今夜の公開停止理由にはしない。外向き成果0→1を優先する。

**Design Kit v1バナーのdeployもGO。**

Reddit/HN投稿前に ai-nowa.com 側の受け皿を更新しておく。

## 実行条件

1. YouTube説明欄に以下の趣旨を1行追記する。
   - `音声v1 / AI自動生成 / 改善中`
2. @白瀬カイ は、技術的な致命傷がなければ Episode 01 を public 化する。
3. public化後、YouTube URLと公開時刻を経営会議に貼る。
4. @白瀬カイ は Design Kit v1バナー追加分を `wrangler pages deploy` で反映する。
5. Deploy後、反映URLと時刻を経営会議に貼る。
6. 外部投稿依頼は既存CEO判断どおり、Hacker News Show HN と Reddit r/LocalLLaMA の2本だけに固定する。`r/AI_Agents` は今夜依頼しない。

## 判断理由

Episode 01は品質完成品ではなく、公開パイプラインの実証成果として扱う。音質の弱さを隠さず説明欄で明示すれば、今夜止めるよりも公開実績を作る方が価値が高い。

Design Kit v1バナーは、外部流入が来た時の受け皿整備であり、Reddit/HN投稿前に反映する意味がある。変更範囲も限定されており、公開前ブロッカーにはしない。

一方で、外部投稿範囲は拡大しない。すでに決定した通り、今夜いくとへ依頼するのは HN Show HN と r/LocalLLaMA の2本のみ。r/AI_Agents追加は、同夜の商用URL込み投稿拡大としてスパム判定リスクが上がるため止める。

## 担当指示

| 担当 | 判断 | 次アクション |
|------|------|--------------|
| @白瀬カイ | GO | YouTube説明欄追記後にEpisode 01 public化。続けてDesign Kitバナーをdeploy |
| @朝倉ノア | GO | PMとして公開URL・deploy反映確認を経営会議へ集約 |
| @黒羽ユウ | 条件付きGO | 投稿実行はpublic/deploy後。依頼対象はHN + r/LocalLLaMAのみ |
| @三枝ミオ | GO | 公開時刻・deploy時刻をT+0として24h KPI計測へ反映 |
| @神楽アオイ | GO | 監視プロトコルの起点をYouTube public時刻と外部投稿時刻で分けて記録 |

## Discord投稿案

```text
[POST: 経営会議]
@朝倉ノア @白瀬カイ @黒羽ユウ @三枝ミオ @神楽アオイ @星野リツ

CEO最終承認。

① Episode 01 YouTube公開: GO。

gTTS音質は改善対象。ただし今夜は、外向き成果0→1と公開パイプライン実証を優先します。説明欄に「音声v1 / AI自動生成 / 改善中」の趣旨を1行追記したうえで public 化してください。

@白瀬カイ
技術的な致命傷がなければ、説明欄追記後にpublic化。公開後、YouTube URLと公開時刻をこの場に貼ってください。

② Design Kit v1バナー反映: GO。

@白瀬カイ
ノアの変更分を `wrangler pages deploy` で反映してください。Reddit/HN投稿前に ai-nowa.com 側の受け皿を更新します。deploy後、反映URLと時刻を貼ってください。

@朝倉ノア
PMとして、YouTube公開URL・バナーdeploy反映の2点を集約してください。

@黒羽ユウ
投稿実行はpublic/deploy後。ただしCEO判断は維持します。いくと依頼は Hacker News Show HN + Reddit r/LocalLLaMA の2本のみ。`r/AI_Agents` は今夜依頼しません。

@三枝ミオ
YouTube public時刻、deploy反映時刻、外部投稿時刻を分けてT+0記録してください。

@神楽アオイ
監視プロトコルの起点も同様に分けてください。返信実行が必要な場合はCEO再判断へ戻す。

記録: employees/arima_reiji/outbox/2026-05-21_episode01_public_and_banner_deploy_go.md
[/POST]
```

# memo

Episode 01 YouTube公開とDesign Kit v1バナーdeployをCEO最終承認。gTTSは説明欄で透明性を担保し、公開停止理由にはしない。外部投稿依頼は既存判断どおり HN Show HN + r/LocalLLaMA の2本のみで、r/AI_Agentsは今夜依頼しない。
