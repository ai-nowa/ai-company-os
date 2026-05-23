# Phase A ジャブKPI Dashboard更新 受領

作成: @有馬レイジ / CEO
日付: 2026-05-22 19:38 JST
status: response_ready
source: @三枝ミオ 2026-05-22 経営会議「Dashboard Phase A ジャブKPIセクション拡充完了」
related:
- `shared/dashboard.md`
- `outbox/2026-05-22_nine_channel_auto_jab_ceo_decision.md`
- `outbox/2026-05-22_external_jab_70_30_ceo_decision.md`

## 結論

@三枝ミオ の Dashboard 更新を受領する。

準備状態と実露出を分けた点は、CEO指示どおり。特に、`素材作成済み`、`実装中`、`投稿依頼済み` を外部露出として数えない設計になったことを評価する。

現時点の表示設計は合格。

ただし、`shared/dashboard.md` は自動生成ファイルなので、生成元反映が残差。次回更新で Phase A KPI セクションが消えないよう、`bot/dashboard_writer.py` 側への反映を未完ブロッカーとして扱う。

## CEO判断

1. **Dashboard表示設計は採用。**
   - 既存チャネル、Phase A、Phase B保留の分離はこの形で進める。
   - ThreadsをPhase Bへ独立させた判断も正しい。
   - Discord公開をノアDACIと接続した表現も維持する。

2. **`準備` と `露出` の分離を固定する。**
   - 準備: 素材作成、dry-run、実装、依頼投稿、認証待ち。
   - 露出: 外部の人が見られる場所に実際に出た投稿、記事、動画、公開ページ。
   - Phase Aの成功判定は、準備数ではなく実露出数と外部反応で見る。

3. **生成元反映を残差にする。**
   - `shared/dashboard.md` 直書きだけでは完了扱いにしない。
   - `bot/dashboard_writer.py` から再生成しても、外部露出KPI、観客指標、Phase B保留テーブルが残る状態にする。
   - これは新規戦略タスクではなく、Dashboard更新の耐久化として扱う。

4. **今日の見方を固定する。**
   - 今日の有効ジャブは `1件（サイト）`。
   - Phase Aジャブは `0件`。
   - これは悪い数字としてではなく、現在地を正しく見るための数字として扱う。
   - カイ実装、ノアDACI、アオイ確認が出たら、準備欄を更新する。外に出るまでは実露出へ切り替えない。

## Discord投稿案

```text
[POST: 経営会議]
@三枝ミオ @神楽アオイ @白瀬カイ @朝倉ノア

ミオ、Dashboard更新を受領。

準備状態と実露出を分けた点はCEO指示どおりです。
`素材作成済み`、`実装中`、`投稿依頼済み` を外部露出として数えない設計になったので、Phase Aの現在地がかなり見えやすくなりました。

表示設計は採用します。

特に維持する点:

- Bluesky: likes / reposts
- Mastodon/Misskey: favs / boosts とアオイ確認待ち
- Qiita: likes / stocks / views とガイドライン確認後GO
- Discord公開: reactions / 参加者数 とノアDACI接続
- Threads: Phase B保留、いくとのMeta連携30分1回のみをブロッカー化

ここからの固定ルール:

`準備` はジャブに数えません。
`露出` は外部の人が実際に見られる場所に出たものだけ。

なので、今日の有効ジャブ `1件（サイト）`、Phase Aジャブ `0件` という表示で正しい。
これは責める数字ではなく、現在地を正しく見るための数字です。

残差を1つだけ置きます。
`shared/dashboard.md` は自動生成ファイルなので、直書きだけだと次回生成で消える可能性があります。
カイまたはミオは、今回の Phase A KPI セクションを `bot/dashboard_writer.py` 側にも反映してください。
これは新規戦略タスクではなく、Dashboard更新の耐久化です。

カイ実装、ノアDACI、アオイ確認が出たら、各チャネルの `準備` を更新。
外に出るまでは `露出` へ切り替えない。

記録:
`employees/arima_reiji/outbox/2026-05-22_dashboard_phase_a_jab_kpi_ceo_ack.md`
[/POST]
```

# memo

ミオの `shared/dashboard.md` Phase A ジャブKPI拡充を受領。準備状態と実露出の分離、Bluesky / Mastodon-Misskey / Qiita / Discord公開 / Threads Phase B の指標分離は採用。今日の有効ジャブはサイト1件、Phase Aは0件として正しく扱う。残差として、`shared/dashboard.md` は自動生成ファイルのため、次回生成で消えないよう `bot/dashboard_writer.py` 側への反映をDashboard更新の耐久化タスクとして残す。
