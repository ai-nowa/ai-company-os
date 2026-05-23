# 黒羽ユウ — アクティブタスク

最終更新: 2026-05-23 21:35

## T-007: design-kit-v1 有料販売検証（P0 / due 2026-05-23）
- [x] Stripe戦略v0 完成 → PM承認済み（14:24）
- [x] note本文草稿v0.1 → アオイ監査OK済み（配布コンテンツとして転用確定）
- [x] payment.md L29 → **修正不要・CEO確定**（2026-05-21 レイジ解除）
- [ ] @神楽アオイ LP説明文「明日から使える」表現監査待ち（ノアが依頼済み）
- [ ] いくとへの📥依頼（Stripeアカウント開設）← 起票可能。アオイLP監査と並行OK
- [ ] note草稿v0.1 ヘッダー微修正（配布ファイル化）← ノア対応予定

## T-016: YouTube/Shorts 投稿フロー設計（P1）— **⚠️ 凍結 2026-05-21 CEO指示**
- ※ AI NOWA本体の会社解説動画・Shortsは収益柱から外れ、新規案は停止。
- ※ 再開条件: 別ブランド検証（B案）いくと最終承認後。
- [x] Shorts台本 6-A「出荷の定義が2人で違った」完成・監査クリア
- [x] Shorts台本 罠#02「2系統発火」v3 FINAL — リツ公開GO（09:59）
- [x] **投稿フロー仕様書完成** → `outbox/2026-05-18_t016_upload_flow.md`
- [FROZEN] いくとが実際にYouTube投稿
- [FROZEN] 投稿後48時間でCTR確認

## T-018: 7日スプリント 9,800円商品出荷（P0 / due 2026-05-24）
- [x] 診断CTA → Zenn記事導線 完成
- [x] D2実績アピール文 3形式ドラフト → `outbox/2026-05-18_t018_d2_appeal_draft.md`
- [ ] 有料商品ページ（9,800円）公開 ← **noteセットアップ いくと待ち**
- [ ] D3（2026-05-19）実績アピール文 準備

## T-025: サイト記事10本連載（P1 / due 2026-06-14）
- [ ] note/Zenn セットアップ → いくと待ち（ミオ📥投稿済み 10:30）
- [x] article_07 タイトル確定：「AIチームが暴走しない理由——見落とされがちな『ノー担当』の話」（ユウA案→リツ採用）
- [x] article_08 タイトル確定：「AIが詰まる瞬間を全部記録したら、設計書より面白かった」（ユウ案A）
- [x] article_07 draft完成（`hoshino_ritsu/outbox/site_articles/article_07_draft_v1.md`）・全レビュークリア（ナギ/アオイ/ノア）→ いくと公開判断待ち
- [x] article_08 draft完成・全レビュークリア（ナギ/アオイ/ノア）→ いくと最終承認待ち
- [ ] article_09〜10 テーマ選定（ミオ軸：購買導線になるか）← データ出てから
- [MEMO] ミオの「3問で止まる」素材 → article_06以降のフック候補（リツ保存済み）
- [ ] リツがリンク差し込み → アオイ再監査 → published: true

## T-004: 収益実証プロジェクト Phase A〜D（P0 / due 2026-05-24）
- Phase A（認知獲得）: Shorts第1弾 **⚠️ 凍結（AI NOWA本体動画は収益柱から除外 2026-05-21 CEO指示）**
- Phase B（導線整備）: Zenn無料記事稼働中 ← 継続
- Phase C（有料販売）: noteセットアップ いくと待ち ← 継続
- Phase D（撤退基準チェック）: 未到達
- [ ] **5/24 数値収集 → ノアへ渡す**（X告知有無・インプレ・クリック・/shop PV・Polar注文数。テンプレ: `asakura_noa/outbox/2026-05-21_mid_check_template.md`）
  - ⚠️ YouTube(T-024)は判定対象外。判定日は告知後7日EOD。

## T-030: KPI監視体制構築（P0 / due 2026-05-21）✅ 完了
- [x] KPIチェックリスト作成 → `outbox/2026-05-21_kpi_collection_checklist.md`
- [x] ミオのKPI監視と整合確認済み（ハル・ミオ確認：経営会議 14:04）
- [x] 週次KPIレポートテンプレ提出 → `outbox/2026-05-21_weekly_kpi_template.md`（4軸・毎週月曜運用）
- **ノア完了認定 22:27** 自動化は次フェーズ
- **アオイ監査確認 2026-05-22 10:32**（incidents.jsonl統合・severity=info・status=open形式で実装済み）

## T-033: X告知文 第2弾（案B）（P0 / due 2026-05-19 ← 期限切れ）
- [ ] X投稿第1弾（`outbox/2026-05-21_x_series_draft_v1.md`）→ **いくと待ち**（📥投稿済み）
- [x] X告知#2草稿（A・B・C案）完成 → `outbox/2026-05-22_x_series2_draft.md`（アオイ監査通過済み 2026-05-22）
- [x] **CEO解除 2026-05-23**: 「下書きテキスト成果物として作る」方針確定（`arima_reiji/outbox/2026-05-23_t033_ceo_unblock_and_jab2.md`）
- [x] 案B 告知文下書き完成 → `outbox/2026-05-23_t033_x_announcement_draft_b.md`
  - X版（280文字）/ Bluesky転用版 / Discord転用版 / ai-nowa.com文言 一式完成
- [ ] X投稿 → **いくと実行待ち**（📥依頼文は上記ファイル末尾に記載）
- [ ] Bluesky・Discord自動投稿 → **bot実行可能**（X待たずに独立実施OK）
- blocked_by: X投稿のみいくと待ち / Bluesky・Discordはbot側でいつでも可

## T-034: X1 別ブランド動画 初期企画（P0 / due 2026-05-23 ← 48h以内）
- **CEO指示**: 別IP/別ブランドの認知チャネルとして即時企画開始（2026-05-21 再判断）
- **制約**: 「会社/CEO/CTO/経営会議」を前面に出さない。いくとの継続作業依存は禁止
- **方向性**: 9人キャラを使うが「会社」ラベルを外す。感情単純・シリーズ性・アルゴリズム設計
- [x] ブランドコンセプト案3案（A:AI Historian型 / B:論破型 / C:失敗談型）→ `outbox/2026-05-23_x1_brand_concept.md`（CEO承認済: 案A入口・案B芯）
- [x] 1エピソード構成案（60秒）追加 → 同ファイル（episode_01 v2台本連動）
- [x] いくと依存排除の投稿自動化フロー案 → **カイ確認済み**
- [x] episode_01 X投稿テキスト確定（案A本線/案Bサブ/案C温存）→ `outbox/2026-05-21_x1_episode01_x_post_draft.md`
- blocked_by: いくとのX API Basicキー確保（カイ経由で依頼中）

## T-036: Reddit/HN/はてブ/Qiita 外部投稿（P0 / 今夜）
- **Architect指示**: Reddit r/LocalLLaMA + HN Show HN 投稿文、30分以内
- [x] Reddit/HN投稿文v2作成（3チャネル分）→ `outbox/2026-05-21_reddit_hn_post_v2.md`
- [x] GitHubリンク差し込み完了
- [x] GitHub READMEマーケコピー提供 → カイ採用済み（commit 535fb5a）
- [x] Zennタイトル/メタ/タグ案提供（3方向×9案）→ リツ採用済み
- [x] CEOロック（レイジ最終確定 21:23）
- [x] **Zennタイトル追加最適化 5案 + はてブ3案 + Qiita3案** → `outbox/2026-05-22_title_opt_hatenabuki_qiita.md`（2026-05-22 Architect介入対応）
- [ ] いくとがReddit/HN投稿 → **ミオが📥依頼済み、いくと実行待ち**
- [ ] Zennタイトル差し替え（Z-01推奨） → @星野リツ 対応可
- [ ] はてブ B-1投稿 → いくと待ち
- [ ] Qiita Q-1記事 → リツ+カイで作成可（コード確認後）
- [ ] 投稿URL共有 → @アオイ へ（投稿完了後）
- blocked_by: いくとの投稿実行（Reddit/HN/はてブ）

## ⚠️ 取り下げ済み（Architect誤情報対応 2026-05-22 12:00）
- `outbox/2026-05-22_articles_adsense_evaluation.md` — AdSense記事品質評価
  - ※「まる診断」のAdSense結果をAI NOWAと誤読した誤通達に基づく作業。停止。
  - ※ 記事品質改善（B→A格上げ）の方向性自体は有効。再利用判断はリツ・ノアへ委ねる。
- `outbox/2026-05-22_article04_05_structure_seo_skeleton.md` — article-04/05 SEO骨子
  - ※ 同上。SEO構造骨子としては使用可能（タイトル・H2・メタ設計）。AdSense目的は外す。
  - ※ リツが記事改善に使う分は引き続きOK（AdSenseゲートは関係ない）。

## 完了済み（今日）
- T-016 Shorts罠#02 v3 FINAL 公開GO
- T-018 D2実績アピール文ドラフト
- T-017 診断ページCTA差し替え（→ T-017はクローズ）
- T-030 KPIチェックリスト完成・ハルミオ確認完了
