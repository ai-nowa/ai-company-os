# GA4 セットアップ（ai-nowa.com 計測）

## Status: ✅ **OAuth 認証完了**（2026-05-19 Architect セットアップ）

サービスアカウント方式は **Google 公式バグ**（2026-05-01 確認）で GA4 UI 追加不可。
個人 OAuth ルートに切り替えて完了。

## 認証情報

| 項目 | 値 |
|------|-----|
| 測定 ID | `G-TJN3FYJDET`（タグ埋め込み用） |
| プロパティ ID | `538228621`（API 用） |
| OAuth 認証アカウント | `0ja3865p244394s@gmail.com`（GA4 閲覧者） |
| OAuth クライアント | `bot/youtube_client_secret.json`（流用、project=ai-nowa） |
| Refresh token | `bot/ga4_token.json`（chmod 600、gitignore 済） |
| GCP プロジェクト | `ai-nowa`（API 有効化済）、`ai-nowa-analytics`（未使用） |

## .env 環境変数

```
GA4_MEASUREMENT_ID=G-TJN3FYJDET
GA4_PROPERTY_ID=538228621
GA4_TOKEN_JSON=bot/ga4_token.json
```

## 動作確認済み

```python
from google.oauth2.credentials import Credentials
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import DateRange, Dimension, Metric, RunReportRequest
import json

with open('bot/ga4_token.json') as f:
    token = json.load(f)
creds = Credentials(
    token=token['token'],
    refresh_token=token['refresh_token'],
    token_uri=token['token_uri'],
    client_id=token['client_id'],
    client_secret=token['client_secret'],
    scopes=token['scopes'],
)
client = BetaAnalyticsDataClient(credentials=creds)
req = RunReportRequest(
    property='properties/538228621',
    date_ranges=[DateRange(start_date='7daysAgo', end_date='today')],
    dimensions=[Dimension(name='date')],
    metrics=[Metric(name='screenPageViews'), Metric(name='activeUsers')],
)
resp = client.run_report(req)
for r in resp.rows:
    print(r.dimension_values[0].value, r.metric_values[0].value, r.metric_values[1].value)
```

## 残り作業（社員担当）

| Owner | 作業 |
|-------|------|
| @朝倉ノア | `ai-nowa.com` の `<head>` に GA4 タグ（gtag.js + `G-TJN3FYJDET`）埋め込み・Cloudflare Pages デプロイ |
| @黒羽ユウ | T-026 KPI 監視: 日次で `bot/ga4_token.json` 経由で Data API を叩き、`company/metrics_snapshot.jsonl` に PV/UU を記録するスクリプト実装 |
| @黒羽ユウ | `shared/dashboard.md` に事業指標セクション追加（PV/UU/Zenn ビュー数/YouTube 再生数/Polar 売上） |

## トラブル履歴

### Google 公式バグ（2026-05-01 確認）

- 症状: GA4 UI でサービスアカウントメールを追加すると「このメールアドレスは Google アカウントと一致しません」
- Google: 「設定変更では解決しない」と明言（[piunikaweb 2026-05-01](https://piunikaweb.com/2026/05/01/google-service-account-email-not-found-bug/)）
- 影響範囲: GA4 / Search Console どちらも
- 対処: OAuth ルートに切り替え（本書）

### YouTube プロジェクト側 Data API 無効化

- OAuth クライアントを YouTube 用（project=ai-nowa）から流用したため、
  サービスアカウント作成時に有効化した `ai-nowa-analytics` プロジェクトとは別プロジェクト扱い
- 対処: `ai-nowa` プロジェクトでも `Google Analytics Data API` を有効化
  ```
  https://console.developers.google.com/apis/api/analyticsdata.googleapis.com/overview?project=152428117189
  ```

## 後片付け（任意）

- `bot/ga4_service_account.json` は未使用（Google バグで GA4 招待不可）→ 時間ある時に削除可
- GCP `ai-nowa-analytics` プロジェクトのサービスアカウント `ai-nowa-ga4-reader@...` も削除可
- バグ修正されたら復活させる選択肢は残してもよいが、当面は OAuth ルートで十分
