# KPI監視レポート v0.2（T-030）
作成: 黒羽ユウ / 2026-05-18 17:40 / 最終更新: 2026-05-20 / due: 2026-05-21
Owner: kuroba_yuu / Buddy: hoshino_ritsu（Zenn view）
ベース計画: `employees/kuroba_yuu/outbox/2026-05-18_metrics_monitoring_plan.md`

**更新履歴:**
- v0 (5/18): 初稿
- v0.1: LS→Polar.sh転換反映・Zenn PV非ログイン不可確認記録
- v0.2 (5/20): A3トライアド判断反映（ノアPM 2026-05-19確定）

---

## 1. 取得スナップショット（2026-05-20 時点）

| チャネル | 指標 | 値 | 取得方法 | 状態 |
|----------|------|-----|---------|------|
| **Zenn** | 記事PV（4本） | **取得不可** | 非ログインでは表示なし（Playwright確認済み 5/18） | 🔴 代替指標へ切替 |
| **Zenn** | 記事URL有効性 | 4本とも200 OK | HEAD リクエスト（zenn_metrics.py実装待ち） | 🟡 カイ実装待ち |
| **YouTube** | 動画再生数 | **公開待ち** | youtube_metrics.py（カイ実装待ち） | 🟡 T-024公開待ち |
| **YouTube** | チャンネル登録者数 | **公開後確認** | YouTube Analytics API（OAuth認証済み） | 🟡 カイ実装待ち |
| **ai-nowa.com /shop** | PV | **Polar OAT後に確認** | Cloudflare Pages Analytics | 🟡 OAT待ち |
| **Polar.sh** | 売上・購入件数 | **販売未開始（OAT待ち）** | Polar管理画面 / API | 🟡 いくとOAT待ち |

**Polar.sh採用（5/18 CEO決定）**: Lemon Squeezy → Polar.sh へ転換済み。980円/件・手取り約881円。

---

## 2. 取得可否を分類（アオイ監査観点）

| カテゴリ | 指標 | 状態 |
|---------|------|------|
| 🟢 取得してよい（公開情報・認証不要） | Zenn記事URL有効性（HEAD request）/ YouTube動画再生数（公開後・ページ） | 即時化可 |
| 🟡 認証必要（既設OAuth・API key） | YouTube Analytics（再生数詳細・登録者・OAuth済み）/ Polar管理画面（OAT後） | スクリプト化 |
| 🔴 いくと依頼必要 | GA4プロパティ作成・gtag.js埋め込み（B1ブロッカー） / Polar OAT発行 | 1回作業 |
| 🔴 **取得不可** | Zenn記事PV（非ログイン状態では表示されない・Playwright確認済み） | 諦める |

---

## 3. 5/21までのアクションプラン

| 期限 | アクション | Owner | 状態 |
|------|-----------|-------|------|
| 5/18 EOD | 本ファイル v0 起票 | ユウ | ✅ |
| 5/18 EOD | Zenn PV取得不可確認（Playwright実機） | ユウ | ✅（非ログインでは取得不可） |
| 5/18 EOD | watched_urls.json 修正（404→実在4本） | ユウ | ✅ |
| 5/19 EOD | `bot/zenn_metrics.py` 実装（URL有効性確認のみ・PVあきらめ） | カイ | 🟡 カイ実装待ち |
| 5/20 EOD | `bot/youtube_metrics.py` 実装（YouTube Analytics API）| カイ | 🟡 カイ実装待ち |
| 5/20 | T-024（罠#02）公開後 → YouTube再生数取得開始 | ユウ | 🟡 いくと待ち |
| 5/21 EOD | 本レポート v1 完成（全チャネル実数値入り） | ユウ | 🔴 カイ実装後 |

---

## 4. dashboard.md 連携設計（v1 で確定予定）

```
## 事業指標（日次・5/21〜）
| 指標 | 直近値 | 前日比 | 取得ソース |
|------|--------|--------|-----------|
| Zenn記事URL有効性（4本） | - | - | zenn_metrics.py（URL 200/404確認） |
| YouTube 再生数（累計） | - | - | youtube_metrics.py |
| YouTube 登録者数 | - | - | youtube_metrics.py |
| Polar.sh 注文数（当月） | - | - | Polar API GET /v1/orders |
| Polar.sh 売上（当月 / 円） | - | - | Polar API × 980円 |
| ai-nowa.com /shop PV | - | - | Cloudflare Analytics（GA4整備まで） |
```

**Zenn PV は取得不可のため、代替指標（URL有効性）に変更。** PV欄は「取得不可（スクレイプ不可）」として記録。

---

## 4.5 転換率計測設計（**A3確定済み 2026-05-19 ノアPM判断**）

購入転換率（目標2%）の計測基盤:

| 要素 | 取得先 | 取得方法 | 状態 |
|------|--------|---------|------|
| 分母: /shop PV | Cloudflare Pages Analytics | 手動確認 or API | 🟢 即使える |
| 分子: Polar注文数 | Polar管理画面 / API `GET /v1/orders` | 手動確認 or カイ実装 | 🟡 OAT発行後 |
| 転換率 = 注文/PV | 手計算（Phase A）| Phase A規模では手動で十分 | 🟢 |

**【確定】Polar Checkout遷移トラッキング: Phase B以降に先送り**  
判断者: 朝倉ノア（PM）/ 2026-05-19  
根拠: Phase A目標3件の規模では離脱率データの統計的意味がない。「/shop PV」+「Polar注文数」の2指標で十分。  
参照: `employees/asakura_noa/outbox/2026-05-19_t030_checkout_tracking_decision.md`

**暫定運用（GA4 B1ブロッカー解消まで）**:
- Cloudflare Analytics の /shop リクエスト数をPV代替として使用
- Phase A「0件か否か」判断には十分。GA4が整備されたら差し替え

---

## 5. 撤退基準への接続（T-004 連動）

- T-030 完了（=数字が1行でも記録される状態）が T-004 Phase A 撤退基準の前提条件
- 5/21時点で全チャネル「N/A 0件」だった場合: 撤退基準の数値判定不能 → ミオCOO判断要請
- 5/24 T-018期限と接続: **Polar.sh注文0件**（旧: LS/Stripe） → Phase A 撤退会議
- **初回購入1件=Phase A成功**（5/18 CEO確定）。980円×3件の基準は廃止

---

## 6. ブロッカー（明示）

| # | 内容 | 解除条件 | 依頼先 | 状態 |
|---|------|---------|--------|------|
| B1 | GA4 未埋め込み（ai-nowa.com PV見えない） | プロパティ作成 + gtag.js埋め込み | いくと（1回作業）| 🔴 未解除 |
| B2 | ~~LS商品未作成~~ → **Polar OAT未発行**（売上計測不可） | Polar.sh OAT（いくと手続き） | いくと | 🔴 いくと待ち |
| B3 | Zenn PV取得不可（非ログインでは表示なし） | **代替: URL有効性確認に切替**（zenn_metrics.py） | カイ | 🟡 方針確定・実装待ち |
| B4 | youtube_metrics.py 未実装 | カイ実装 | カイ（5/20 EOD目標）| 🟡 カイ実装待ち |

---

## 次のアクション

- [x] Zenn PV取得不可確認 → URL有効性確認に方針転換（5/18）
- [x] watched_urls.json 修正（4本に更新・5/18）
- [x] カイへzenn_metrics.py + youtube_metrics.py実装依頼（5/18）
- [x] A3トライアド Checkout追跡判断：ノアPM確定（Phase B以降・5/19）
- [ ] Polar OAT発行後 → /shop PV + 注文数の初回確認（いくと待ち）
- [ ] カイのzenn/youtube_metrics実装完了後 → metrics_snapshot.jsonlから本ファイルに反映
- [ ] 5/21 EOD: v1完成（全チャネル実数値・dashboard連携）

---

5/21 v1で「全チャネル実数値 + 日次取得可能状態」を目指す。

---

## 追記（metrics.csv 方針 v0.2更新）

`company/metrics.csv` のカラム: `timestamp, source, key, value, unit, note`

5/20時点での登録予定行:

| source | key | value | note |
|--------|-----|-------|------|
| zenn | article_v01_url_status | 200 | URL有効性のみ（PV取得不可） |
| zenn | article_v02_url_status | 200 | 同上 |
| zenn | article_v03_url_status | 200 | 同上 |
| zenn | ainowa-design-kit-intro_url_status | 200 | 同上 |
| polar | orders_total | PENDING | OAT待ち |
| polar | revenue_jpy | PENDING | OAT待ち |
| youtube | subscribers | PENDING | カイ実装待ち |
| youtube | views_total | PENDING | T-024公開後 |

**旧: lemonsqueezy.orders / lemonsqueezy.revenue → 削除**（Polar転換で不要）

