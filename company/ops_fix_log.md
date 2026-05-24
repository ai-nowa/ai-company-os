# Ops Fix Log

## 2026-05-25 08:07 JST

- コミット: `e825064 Stabilize revenue path and token guards`
- 解決した問題:
  - Claude Code が `rc=0` かつ空出力で返った時、通常エラー扱いで再発し続けていたため、Claude unavailable としてサーキット対象に変更。
  - 重要メンションで即時起動数が暗黙に4人へ膨らんでいたため、動的設定 `mention_chain.high_priority_mentions_per_response` に統一。
  - 直近60分の prompt_chars が `mention_chain.overheat_prompt_chars` を超えた時、メンション連鎖の即時起動を `mention_chain.overheat_keep_targets` 人に抑え、残りを inbox 退避する過熱ガードを追加。
  - Revenue Board の YouTube Analytics 未取得記述を修正し、再認可済み・再起動後の集計を正とする状態に更新。
  - KPI集計で「価格調整中」を未取得扱いしていたため、価格状態として記録するよう修正。
  - Polar Downloadables 添付をCLI化し、dry-runを標準、本番添付は明示確認必須にした。
  - Polar checkout をコード定数ではなく `POLAR_CHECKOUT_ENABLED` 環境変数で明示ONできるようにした。
- 検証:
  - `bot/.venv/bin/python -m pytest bot/tests` → 77 passed
  - `node --check site/functions/api/polar/create-checkout.js` → OK
  - `bot/.venv/bin/python -m bot.polar_client products` → Polar商品2件を読み取り確認、どちらも benefits=0
  - `bot/.venv/bin/python -m bot.polar_client attach-downloadable ...` dry-run → `/tmp/design-kit-v1_preaudit.zip` の payload/benefit 構築OK、本番変更なし
  - `bot/.venv/bin/python -m bot.external_metrics` → YouTube Analytics 取得OK、shop price=`価格調整中`
- 再起動:
  - dispatcher を `bot.dispatcher_manager restart` で再起動。
  - 新PID: `1857818`
  - 9社員 client ready をログで確認。

## 次の売上導線ゲート

1. 最終ZIPを監査済みとして確定。
2. 価格をCEO/マーケで確定。
3. Polar Downloadables を sandbox live で疎通。
4. アオイ監査GO後に本番添付。
5. `POLAR_PRODUCT_ID` と `POLAR_CHECKOUT_ENABLED=1` を設定し、shop表示と価格を一致させて公開。
