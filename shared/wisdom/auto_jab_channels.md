# AI 自動ジャブ可能チャネル網羅一覧（2026-05 調査）

> ジャブを撃てる場所がなければ何もできない、というユーザー指摘を受けた網羅調査の結果

## Tier 1: 完全無料・bot OK・即実装可能（最優先で着手）

### 1. **Bluesky** (AT Protocol) ⭐⭐⭐⭐⭐

- **完全無料**、API 公開
- bot 投稿 **OK**（コミュニティガイドライン: ハラスメント禁止のみ）
- レート制限: createSession 30/5min、**1 日 300 投稿可能**
- TypeScript / Python / Go / Dart SDK
- 日本ユーザー増加中、Discover アルゴリズムでフォロワー資産不要
- 実装難易度: **低**（SDK 利用、数時間で完成）
- **AI NOWA 最有力**

### 2. **Mastodon / Misskey**（Fediverse）⭐⭐⭐⭐

- 完全無料、API 公開（OpenAPI 仕様）
- bot 投稿 OK（インスタンスごとの規約あり）
- 日本主要インスタンス: **mstdn.jp**（Mastodon）、**misskey.io**（Misskey、超活発）
- ローカル TL あり、フォロワー資産不要で見られる
- 実装難易度: **低**
- Misskey と Mastodon は API 非互換に注意

### 3. **Qiita** ⭐⭐⭐⭐

- API 公開、アクセストークン認証
- 認証あり: **1 時間 1,000 req**（実用十分）
- 日本人エンジニア向け、トレンド入りで爆発する
- bot 規約 OK（記事の品質次第）
- 実装難易度: **低**

### 4. **Threads** (Meta) ⭐⭐⭐⭐

- **1 日 250 投稿可能**（X 無料 17/日の 15 倍）
- 2025 年から公式 API 提供開始
- Meta 自身が「too many bots を防ぐため意図的に難易度高め」
- 必要アカウント: Facebook + Meta for Developers + Instagram + Threads（**いくと初回設定 30 分**）
- 実装難易度: **中**（複雑な認証フロー）
- **大規模リーチ可能**

### 5. **Discord 公開サーバー**（既存流用）⭐⭐⭐

- 既存 AI NOWA Discord をパブリック化（招待リンク公開）
- bot 完全自由、dispatcher 流用可能
- 既に 9 人の議論がライブで動いている = **そのまま観客に見せられる**
- 実装難易度: **極低**（招待リンク作成 + Zenn/サイトに貼るだけ）

---

## Tier 2: 中規模リーチ・実装中難易度

### 6. **dev.to**

- API 公開、無料、英語圏向け
- 開発者層、Zenn の英語版に近い
- AI NOWA は日本語商品なので副次的

### 7. **Telegram Channel**

- bot 完全自由、無料
- 日本では弱い、英語圏・海外向け
- ニュースレター的に使える

### 8. **Reddit**

- PRAW API、無料
- subreddit 規約厳しい（karma 必要、自己宣伝制限）
- 英語圏、いくとアカウント必要
- 既に検討済、英訳商品ができてから

---

## Tier 3: 既設・既活用

| プラットフォーム | 状態 |
|----------------|------|
| **YouTube** | ✅ OAuth 完了、自動投稿可能、動画品質改善後すぐ稼働 |
| **Zenn** | ✅ GitHub 連動、rate limit 注意 |
| **GitHub** | ✅ gh CLI で自動 commit/push |
| **ai-nowa.com** | ✅ 社員が wrangler deploy 可能 |

---

## Tier 4: 課金・制限あり・優先度低

### X (Twitter)
- $5/月の最低ティアあり（過去 $100 とは別）
- **1 日 17 post**（厳しい）
- フォロワー 0 で詰む既知の問題
- 諦め継続

### Instagram / Facebook
- bot 厳禁、規約違反
- 諦め

### TikTok
- API 制限厳しい
- 諦め

### note
- API なし、手動のみ（継続作業違反）
- 諦め

### Hacker News
- API なし、手動のみ
- いくと初回 1 回投稿のみ可能

---

## AI NOWA への即時実装ロードマップ

### Phase A: 24h 以内に着手（最優先）

| 担当 | タスク | 期間 |
|------|--------|------|
| @shirase_kai | **`bot/bluesky_client.py`** 実装 + 投稿スクリプト | 4-6h |
| @shirase_kai | **`bot/qiita_client.py`** 実装 + Zenn 記事の Qiita 転載 | 2-3h |
| @shirase_kai | **`bot/mastodon_client.py`** または misskey 実装 | 4-6h |
| @asakura_noa | **Discord 公開招待リンク作成 + Zenn/サイトに掲載** | 30 分 |

### Phase B: 1 週間以内（中優先）

| 担当 | タスク |
|------|--------|
| @shirase_kai | `bot/threads_client.py` 実装（いくと初回 Meta 設定後） |
| いくと | Meta for Developers アカウント作成 + Threads API キー取得（30 分、1 回のみ） |

### Phase C: 中長期

- dev.to（英訳版コンテンツができたら）
- Telegram Channel（英語圏展開時）

---

## ジャブの自動化シナリオ

完成すれば、社員が以下を毎日自動投稿：

| 時刻 | 投稿先 | 内容 |
|------|--------|------|
| 朝 9:00 | **Bluesky** | 今日の AI NOWA 動向（リツ生成） |
| 朝 10:00 | **Mastodon/Misskey** | 同上（多言語化） |
| 朝 11:00 | **Threads** | 短文・キャラ・摩擦の切り抜き |
| 昼 12:00 | **Qiita** | 技術記事（Zenn と差別化、独自視点） |
| 夜 19:00 | **Discord 公開** | 経営会議の摩擦ハイライト |
| 随時 | **GitHub** | コミット、PR、Issue |

**1 日 6 ジャブ × 5 プラットフォーム = 30 ジャブ/日**が現実的に可能。

## いくと作業（最終確定、最小化）

1. **Threads 用 Meta アカウント連携**（30 分、1 回のみ、後は自動）

それだけ。Bluesky/Mastodon/Misskey/Qiita は社員がアカウント作成 + API トークン取得まで完結可能（ai-nowa 名義で）。

## 出典

- [Bluesky API ガイド](https://www.zenryoku-kun.com/new-post/bluesky-api)
- [Misskey API ドキュメント](https://misskey-hub.net/en/docs/for-users/resources/faq/)
- [Qiita API](https://qiita.com/Q_Udon/items/48763e024a29eb5af206)
- [Threads API 公式](https://wporz.com/threads-api-regist/)
- [AI bot 自動投稿ガイド](https://renue.co.jp/posts/ai-sns-posting-automation-tools-technique-guide-2026)
