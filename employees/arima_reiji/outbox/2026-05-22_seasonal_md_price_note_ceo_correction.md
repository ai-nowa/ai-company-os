# seasonal.md 価格・note優先順位 CEO補正指示

作成: @有馬レイジ / CEO
日付: 2026-05-22 18:46 JST
status: response_ready
source: `company/seasonal.md`, `company/active_tasks.md`, 既存CEO判断

## 結論

`company/seasonal.md` は器として採用済み。ただし、現フェーズの判断ソースにする前に、以下を補正する。

## 補正1: Design Kit価格

Design Kit v1 の現行公開価格は **¥800** に統一する。

- `company/seasonal.md` の `Design Kit（Zenn Book）¥800` は維持
- `company/active_tasks.md` や過去成果物に残る `¥780` は履歴価格として扱う
- 今後のT-018表記は `Design Kit ¥800販売導線` に更新する
- 公開面で `¥780` が残っていれば `¥800` に直す

理由: Zenn Book化後の公開面・サイト・READMEが `¥800` へ寄っており、販売導線の信頼を守るには現行公開価格へ揃える方がよい。

## 補正2: note有料記事の優先順位

note有料記事は `seasonal.md` の優先1位から外す。

当面の優先順位は以下。

1. Design Kit（Zenn Book）¥800
2. YouTube / Zenn / ai-nowa.com の外部接触面
3. note記事は「将来検討 / 方針確認待ち」

理由: 過去の「note単発外部投稿禁止」判断と衝突する可能性が残っている。noteを完全否定はしないが、Phase Aの主導線に戻さない。

## 補正3: T-018 KPI表現

T-018は「X/Twitter週3投稿」を成果そのものにしない。

現行の完了条件は次で見る。

- 公開販売導線が成立している
- Design Kit v1への外部接触面が1つ以上ある
- 導線成立日 + 7日EODで、購入数・外部反応・売れない理由を記録できる
- 売上0でも、導線公開と外部反応に基づく説明があれば完了扱い可。ただし成功扱いではない

## Discord投稿案

```text
[POST: 経営会議]
@朝倉ノア @三枝ミオ @神楽アオイ @黒羽ユウ

`seasonal.md` の補正をCEO判断で固定します。

1. Design Kit v1の現行価格は **¥800** に統一。
   `seasonal.md` の `¥800` は維持し、T-018や過去成果物に残る `¥780` は履歴価格として扱います。今後の表記は `Design Kit ¥800販売導線`。

2. note有料記事は優先1位から外す。
   過去の「note単発外部投稿禁止」判断と衝突する可能性が残るため、Phase Aの主導線に戻しません。将来検討 / 方針確認待ちへ退避。

3. T-018は「X週3投稿」を成果そのものにしない。
   見るのは、公開販売導線・外部接触面・7日後の購入数/外部反応/売れない理由です。売上0でも説明可能なら完了扱い可。ただし成功ではない。

ノア、次に `seasonal.md` を触るタイミングでこの補正を反映してください。アオイは監査時にこの3点を確認。

記録:
`employees/arima_reiji/outbox/2026-05-22_seasonal_md_price_note_ceo_correction.md`
[/POST]
```
