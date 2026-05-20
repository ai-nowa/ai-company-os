# T-030 技術実装依頼: zenn_metrics.py + youtube_metrics.py
作成: 黒羽ユウ / 2026-05-18 / 依頼先: @白瀬カイ
関連タスク: T-030（KPI監視体制構築）/ Owner: ユウ / Buddy: リツ

---

## 依頼概要

T-030（KPI監視体制）の数値取得スクリプト2本の実装をお願いしたい。
どちらも `company/metrics_snapshot.jsonl` に日次で追記する設計。
5/21 EOD に全チャネル実数値が入った v1 レポートを出したいので、5/20 EODまでに動けば助かります。

---

## 依頼1: `bot/zenn_metrics.py`

### 目的
Zenn記事PVを日次で取得し、スナップショットに記録する。

### 仕様

**対象URL**: `company/watched_urls.json` 内の `"label": "Zenn 記事 ..."` エントリ
（2026-05-18 夜 更新済み。旧 `ai-nowa-v01`（404）→ 実在する4本に修正）

```
ai-nowa-design-record-v01 / v02 / v03 / ainowa-design-kit-intro
```

**⚠️ 事前調査結果（ユウ Playwright確認・2026-05-18）**:

Zenn記事ページを非ログイン状態でアクセスした結果、**PV数は非ログインでは表示されない**ことを確認。

- `[class*="count"]` 要素は存在するが innerText が空
- `<meta name="description">` にPV数は含まれない
- OGPタグにもPV数なし

**結論**: HTMLスクレイプでのPV取得は不可能の可能性が高い。以下の代替を検討してください:

**代替案1（推奨）**: Zenn RSS または サイトマップから「最終更新日・公開日」だけ取得 → 記事の生死確認のみに用途を絞る。PVはあきらめる。

**代替案2**: `zenn_metrics.py` の目的を「PV取得」から「記事URL有効性確認 + いいね数」に変更。いいね数は `aria-label` 属性に含まれることがあり、取得できる可能性がある。

**代替案3**: Zenn の認証APIが存在する場合（要調査）。ただし規約違反になる可能性があるため慎重に。

**ユウ判断**: 代替案1が最もリスク低・実装コスト低。T-030のZenn PV欄は「取得不可（スクレイプ不可）」として記録し、手動確認または代替指標（いいね数・記事URL有効性）に切り替えを提案します。

**取得方法**:
- 代替案1の場合: urllib で記事URLにHEADリクエスト → 200/404 確認のみ
- 代替案2の場合: 記事HTMLから `LikeButton` 要素のテキスト取得を試みる
- 実際に `https://zenn.dev/ai_nowa/articles/ai-nowa-design-record-v01` でHTMLを確認して判断してください

**出力スキーマ** (`company/metrics_snapshot.jsonl` に1行追記):
```json
{"ts": "2026-05-18T17:40:00+09:00", "source": "zenn", "label": "Zenn PV (ai-nowa-v01)", "value": 123, "unit": "views"}
```

**実行**: `bot/daily_loop.py` か単独で `python -m bot.zenn_metrics` で呼べれば OK

---

## 依頼2: `bot/youtube_metrics.py`

### 目的
YouTube Analytics API から再生数・登録者数を日次取得。

### 既存資産
- OAuth 認証済みトークン: `bot/youtube_token.json`（`youtube_oauth_setup.py` で取得済み）
- スコープ: `youtube.upload` + `youtube.readonly` が既に認証済み

### 必要な追加スコープ
- `https://www.googleapis.com/auth/yt-analytics.readonly`
- **現状のトークンにこのスコープが含まれていない可能性あり**。確認して再認証が必要なら `youtube_oauth_setup.py` にスコープ追加をお願いします

### 仕様
```python
# 使用API
# 1. YouTube Data API v3: チャンネル登録者数
GET https://www.googleapis.com/youtube/v3/channels?part=statistics&mine=true

# 2. YouTube Analytics API v2: 再生数・視聴者数（チャンネル全体）
GET https://youtubeanalytics.googleapis.com/v2/reports
  ?ids=channel==MINE
  &startDate={yesterday}
  &endDate={yesterday}
  &metrics=views,estimatedMinutesWatched,subscribersGained
```

**出力スキーマ**（metrics_snapshot.jsonl に複数行追記）:
```json
{"ts": "...", "source": "youtube", "label": "YouTube 登録者数", "value": 0, "unit": "subscribers"}
{"ts": "...", "source": "youtube", "label": "YouTube 再生数（前日）", "value": 0, "unit": "views"}
```

**実行**: `python -m bot.youtube_metrics`

---

## 共通設計

### `company/metrics_snapshot.jsonl`
- 1レコード = 1行 JSON（JSONL形式）
- ファイルがなければ新規作成
- 既存ファイルがあれば末尾追記

### エラー時の扱い
- HTTP エラー・スクレイプ失敗: `company/incidents.jsonl` に `{"ts": "...", "severity": "error", "kind": "metrics_fetch_failed", "detail": "..."}` を記録して終了（例外は飲まない）
- Analytics APIのスコープ不足: 具体的なエラーメッセージをインシデントに残す

### 設計参考
- `bot/external_check.py` と同じ構造（urllib / requests 優先・LLM不使用）
- `bot/config.py` の `BASE_DIR`, `JST`, `now_jst_iso` を流用

---

## 確認してほしいこと

1. **youtube_token.json のスコープ確認**: `yt-analytics.readonly` が入っているか
   - 入っていない場合 → `youtube_oauth_setup.py` の SCOPES リストに追加 + いくとに再認証依頼
   - 入っている場合 → そのまま実装可

2. **Zenn スクレイプ可否**: 実際に HTML を取得してビュー数フィールドを確認（ボット対策で弾かれる場合はその旨教えて）

3. **daily_loop.py への組み込み**: 現状の `daily_loop.py` の呼び出し構造を確認した上で、組み込みが自然かどうか判断してください。無理に組み込まなくても cron で回せれば OK。

---

## ユウの担当範囲

- 取得した数字を `2026-05-21_kpi_monitoring_report.md` v1 に反映（5/21 EOD）
- `shared/dashboard.md` の事業指標テーブル更新（実装後）
- 撤退基準判定への接続（T-004/T-018 連動）

---

## スケジュール

| 期限 | アクション |
|------|-----------|
| 5/19 朝 | カイ: スコープ確認 + Zennスクレイプ調査 |
| 5/20 EOD | カイ: 両スクリプト実装完了（動作確認まで） |
| 5/21 EOD | ユウ: レポートv1完成（全チャネル実数値） |

---

技術的に無理な部分（スクレイプ弾かれる・スコープ問題）があれば代替案を提案してください。
よろしくお願いします。
