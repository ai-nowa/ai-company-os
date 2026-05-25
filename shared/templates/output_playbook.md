# Output Playbook

目的: AI NOWA の成果を「内部メモ」ではなく、公開・販売・計測できる形に閉じる。

## 成果の定義

成果として数える:
- 公開URL
- 販売ページ/購入導線
- 投稿URL
- YouTubeなど外部プラットフォームの公開/限定公開URL
- 計測可能なデプロイURL
- 顧客反応、購入意向、問い合わせ、返信などの外部シグナル

成果として数えない:
- CEO ack
- PMまとめ
- 監査メモ
- 投稿依頼だけ
- 「明日確認」
- 「いくと待ち」

## 出口優先順位

1. 既に自動投稿/自動公開の認証があるチャネルで出す。
2. 認証がないチャネルが本命でも、同じ素材を認証済みチャネルへ転用する。
3. 外部投稿が全部止まる場合は、ai-nowa.com の短報・記事・shop導線へ出す。
4. 公開できない理由が法務/安全/権利なら、監査ファイルに blocked_by と代替案を残す。

## 実行ルート早見表

迷ったら上から順に試す。通常作業を `いくと依頼` に投げない。
機械判定の正本は `company/output_route_status.json`。公開済み判定の正本は `company/shipped_artifacts.jsonl`。

| ルート | 使う時 | 実行 |
|---|---|---|
| ai-nowa.com site | 記事・短報・導線・shop/about | `site/public/...` を更新 → `cd site && wrangler pages deploy public --project-name=ai-nowa --branch=main --commit-dirty=true` |
| site article | 監査OKの記事 | `site/public/articles/article-XX/index.html` と `site/public/articles/index.html` を更新 |
| site note | X/YouTube/Blueskyが止まった素材 | `site/public/notes/<slug>/index.html` に短報化 |
| Bluesky | 300字以内の告知 | `bot/.venv/bin/python -m bot.bluesky_client --text "..."` |
| YouTube | mp4とOAuth tokenがある | `bot/.venv/bin/python -m bot.youtube_upload --video <mp4> --title "..." --privacy unlisted` |
| Zenn | `articles/<slug>.md` と監査lockがある | `bot/.venv/bin/python -m bot.zenn_publisher <slug>` |
| X | API実投稿不可/未確定 | `bot.x_publisher` はdry-run扱い。人間待ちにせずBlueskyかsite noteへ転用 |

失敗したら「失敗したルート」「理由」「代替公開パス」を `成果物報告` に残す。
公開できたら `source_path / route / output_url / executor / verified_at` を `company/shipped_artifacts.jsonl` に残す。これがない成果物は、あとで再び未出荷在庫に戻る。

## ルート別完了条件

### site article

1. 既存slugと番号を確認する。
2. MarkdownをHTMLに変換し、`site/public/articles/article-XX/index.html` に置く。
3. `site/public/articles/index.html` に追加する。
4. `cd site && wrangler pages deploy public --project-name=ai-nowa --branch=main --commit-dirty=true` を実行する。
5. `curl -I -L https://ai-nowa.com/articles/article-XX/` と本文文字列確認を行う。
6. 成果物報告と shipped_artifacts にURLを記録する。

### YouTube

1. mp4、title、description、privacy、AI生成/改変コンテンツ開示方針を揃える。
2. `bot/youtube_token.json` と `youtube.upload` scope を確認する。
3. **音声品質ゲート**（`company/youtube_audio_quality_policy.md`）を通す。`--privacy public` は engine=silent/gtts または無音/clipping違反で block。FAIL時は再生成してから公開する。
4. `bot/.venv/bin/python -m bot.youtube_upload --video <mp4> --title "..." --privacy unlisted` を実行する。
5. `shared/media/upload_results/*.json` の `dry_run=false` と `url` を確認する。
6. URLが出ない場合は、人間待ちではなく台本/静止画/要約を site note へ転用する。
7. YouTube Studio側のAI開示UIなどAPI外の操作だけ、失敗証跡つきで `[HUMAN_REQUIRED]` にする。

### Bluesky / X代替

1. X投稿待ちは成果物ではない。
2. 同じ本文を `bot/.venv/bin/python -m bot.bluesky_client --text "..."` で出す。
3. Bluesky失敗時は `site/public/notes/<slug>/index.html` に短報化する。
4. bsky URLまたはsite note URLを shipped_artifacts に記録する。

## チャネル別テンプレ

### X が止まる時

- やらないこと: 「いくと投稿待ち」で停止
- やること:
  - 同じ本文を Bluesky / 公開Discord / サイト短報へ転用
  - `ai-nowa.com/about` と `ai-nowa.com/shop` の導線を残す
  - 計測条件を `about PV` / `shop PV` / 返信 のどれかにする

### YouTube が止まる時

- やらないこと: 動画ファイルを outbox に置いたままにする
- やること:
  - OAuth token があるなら YouTube upload を実行候補にする
  - token が壊れているなら、動画のサムネ/台本/短い引用をサイト短報へ転用
  - 必ず公開URLまたは代替公開パスを `company/release_board.md` に残す

### 記事が止まる時

- やらないこと: note/Zennの都合で記事そのものを止める
- やること:
  - 監査済みなら `site/public/articles/` に出す
  - 末尾に `/about` と `/shop` の導線を入れる
  - 公開URLを成果物報告へ出す

### 販売ページが止まる時

- やらないこと: 決済未完了だけで販売仮説を止める
- やること:
  - 価格、内容、CTA、購入意思フォームのどれが検証対象か1つに絞る
  - `/shop` PV を最小成功として導線を1本追加
  - 決済が止まるなら購入意思フォームを暫定シグナルにする

## Discord 投稿テンプレ

```md
[POST: 成果物報告]
Release:
- 出したもの:
- 公開URL/パス:
- 対象実験:
- 計測条件:
- 次の判断:
[/POST]
```

## 禁止文

- 明日朝確認します
- 今日はいったんここまで
- いくと投稿待ちです
- 反応が出たら考えます
- 公開判断待ちです

必要ならこう書く:

- 本命チャネルは未認証のため、同素材を認証済みの `X` ではなく `site/Bluesky/YouTube/Zenn` へ転用する
- まだ外部反応はない。だから今の最小成功は `shop_view >= 1` に置く
- 人間待ちを市場反応ゼロとして扱わない。ただし会社は止めず、代替出荷を今行う
