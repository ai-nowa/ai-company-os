# YouTube public化 依頼
作成: 白瀬カイ / 2026-05-21
宛先: いくと
所要時間: 2〜3分

---

## 状況

episode_01 は YouTube に unlisted（限定公開）でアップロード済み。
privacy status を public に変更するには `youtube` フルスコープが必要だが、
現在の token は `youtube.upload` スコープのみのため API から変更不可。

---

## いくとへの依頼（2択）

### 方法A: YouTube Studio で手動変更（推奨・2分）

1. https://studio.youtube.com を開く
2. 左メニュー「コンテンツ」→ 動画一覧
3. 「先延ばし、あなたがやめられない本当の理由 | AI NOWA #01」を選択
4. 「詳細」→「公開設定」→「公開」に変更
5. 保存

### 方法B: token 再作成 + カイが API 実行（5分）

1. `bot/youtube_token.json` を削除
2. `cd /home/ikuto/ai-company-os && bot/.venv/bin/python bot/youtube_oauth_manual.py` を実行
3. ブラウザでGoogle認証（scope: youtube フルアクセス）
4. カイが `videos.update` API で public 化

---

## 完了後にDiscordで教えてください

「YouTube public化完了」と一言もらえれば、カイが経営会議に集約報告します。

動画URL: https://youtu.be/rtG6ukWeMX8
