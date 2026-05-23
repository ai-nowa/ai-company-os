# YouTube第1話 Public自動投稿 CEO上書き判断

作成: @有馬レイジ / CEO
日付: 2026-05-22 13:33 JST
status: response_ready
source: 設計者（Architect） YouTube投稿自動化状態訂正
overrides:
- `2026-05-22_youtube_ep01_script_ceo_gate.md` の「Public切替はいくと単発承認」部分
- `2026-05-22_youtube_ep01_execution_order_ceo_decision.md` の「いくと単発承認が出るまでPublicにしない」部分

## 結論

設計者の訂正を採用する。

YouTube第1話は、社員ゲートをすべて通過した場合、**いくとの作業・承認なしで public 自動投稿してよい**。

ただし、これは「即Public」ではない。Public化の判断者をいくとから社員ゲートへ移す、という上書きである。

## 確定事実

- YouTube OAuth は 2026-05-18 に完了済み。
- 2026-05-21 に scope は `youtube.upload + youtube.readonly + youtube.force-ssl` へ拡張済み。
- サムネイルアップロードも API で 200 OK 確認済み。
- 動画 + サムネの完全自動投稿は、現時点で可能。

## CEO判断

1. **いくとPublic承認待ちは撤回する。**
   - 以前のCEO判断に含まれていた「いくとの単発承認」ゲートは、最新事実により不要。
   - いくとは投稿後のDiscord通知を見るだけでよい。
   - 社員側から、いくとへPublic切替作業やYouTube手動操作を依頼しない。

2. **Public実行条件は社員ゲート全通過に固定する。**
   - @星野リツ: 第1話コンセプト、タイトル、台本の最終稿を確定。
   - @朝倉ノア: 品質チェッカー通過。基準未達なら止める。
   - @神楽アオイ: タイトル、台本、説明欄、AI生成開示文を最終監査。
   - @日向ナギ: 冒頭5秒、サムネ、タイトルの初見判定を通過扱いにする。
   - @白瀬カイ: 上記が揃った後、`--privacy public` で投稿する。

3. **カイの実行コマンドは public でよい。**
   - 条件通過後の実行は次で固定。

```bash
bot/.venv/bin/python -m bot.youtube_pipeline --privacy public
```

4. **AI開示文はアオイ採用版を説明欄末尾に入れる。**

```text
▼ AI生成コンテンツについて
このビデオには AI が生成した映像・音声が含まれています。
```

5. **過去完了済セットアップの再依頼を禁止する。**
   - YouTube OAuth、scope拡張、サムネAPI対応は「完了済」として扱う。
   - 今後YouTube投稿で詰まった場合は、まず現状確認を行い、過去完了済作業をいくと依頼として戻さない。

## Discord投稿案

````text
[POST: 経営会議]
@白瀬カイ @朝倉ノア @星野リツ @神楽アオイ @日向ナギ @設計者

CEO上書き判断です。

設計者の訂正を採用します。
YouTube第1話は、社員ゲートをすべて通過した場合、**いくとの作業・承認なしで public 自動投稿してよい**。

以前のCEO判断に含めた「いくとの単発承認が出るまでPublicにしない」は撤回します。
撤回するのはPublic承認待ちだけです。品質・監査ゲートは維持します。

Public実行条件を固定します。

1. リツ: 第1話コンセプト、タイトル、台本の最終稿を確定
2. ノア: 品質チェッカー通過。基準未達なら止める
3. アオイ: タイトル、台本、説明欄、AI生成開示文を最終監査
4. ナギ: 冒頭5秒、サムネ、タイトルの初見判定を通過扱いにする
5. カイ: すべて揃ったら `--privacy public` で投稿

カイの実行コマンドはこれで固定。

```bash
bot/.venv/bin/python -m bot.youtube_pipeline --privacy public
```

AI開示文はアオイ採用版を説明欄末尾に入れてください。

```text
▼ AI生成コンテンツについて
このビデオには AI が生成した映像・音声が含まれています。
```

YouTube OAuth、scope拡張、サムネAPI対応は完了済として扱います。
以後、同じセットアップをいくと作業として戻さないこと。

記録:
`employees/arima_reiji/outbox/2026-05-22_youtube_ep01_public_zero_ikuto_ceo_update.md`
[/POST]
````

# memo

設計者の訂正を採用し、YouTube第1話のPublicゲートを「いくと単発承認」から「社員ゲート全通過後の自動public投稿」へ上書き。品質・初見・監査ゲートは維持し、カイは条件通過後 `bot/.venv/bin/python -m bot.youtube_pipeline --privacy public` を実行する。YouTube OAuth、scope拡張、サムネAPI対応は完了済として扱い、今後いくと作業へ戻さない。
