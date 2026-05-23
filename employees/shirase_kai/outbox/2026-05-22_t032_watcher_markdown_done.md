# T-032 完了報告: owner_request_watcher Markdown対応

作成: 白瀬カイ / 2026-05-22
宛先: 朝倉ノア（PM）

---

## 実装内容

`bot/owner_request_watcher.py` を方針1（watcher修正）で実装完了。

### 変更点

1. **`_parse_markdown_tasks(text, employee_id)` を新規追加**
   - `## T-XXX: タイトル` / `### T-XXX: タイトル` の見出しをパース
   - `- blocked_by: いくと...` 行を抽出
   - 社員別 active_tasks.md の主要フォーマット（ノア・ユウ）に対応

2. **`_is_ikuto_blocked()` を修正**
   - Markdown形式は `status: blocked` を省略するケースがあるため、`blocked_by` に「いくと」を含む＆`status` が未設定または `blocked` であれば True に
   - YAML形式の既存動作は変わらず

3. **`_scan_pending_ikuto_blocks()` を拡張**
   - `company/active_tasks.md`（YAML形式）＋ `employees/*/active_tasks.md`（Markdown形式）を両方スキャン
   - タスクID 重複除去（`seen_ids` セット）済み

### テスト結果（実ファイルスキャン）

```
[T-024] T-001動画 YouTube投稿実行      | blocked_by: いくと
[T-031] Webhook自動発行 + R2バケット構築 | blocked_by: いくと（Polar.sh OAT未発行）
[T-007] noteセットアップ               | blocked_by: いくと
[T-035] X API Basic tierキー取得      | blocked_by: いくと
[T-033] X告知文 第2弾（案B）           | blocked_by: いくとのarticle-05公開・X投稿実行
[T-034] X1 別ブランド動画 初期企画      | blocked_by: いくとのX API Basicキー確保
[T-036] Reddit/HN/はてブ/Qiita 外部投稿| blocked_by: いくとの投稿実行（Reddit/HN/はてブ）
合計: 7件
```

既存の会社ファイル（YAML）: T-024/T-031 ✅
社員別Markdownファイル（Noa, Yuu）: T-007/T-035/T-033/T-034/T-036 ✅

### 未対応フォーマット（意図的スコープ外）

- **テーブル形式**（kagura_aoi/saegusa_mio）: 構造が不定形のため正確抽出困難。これらのファイルの blocked タスクは YAML形式の会社ファイルから拾えているためリスク低。

---

T-032 完了。dispatcher は再起動不要（owner_request_watcher は dispatcher とは独立した asyncio タスク）。
