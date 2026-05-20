# Phase 3 展開時に社員 system prompt に追加するセクション

Phase 2（mio 1名でテスト）が成功したら、`bot/employee_runner.py:build_employee_system_prompt` の「サブエージェント」セクション直後に下記を挿入する。

## 挿入箇所

```python
"## agentmemory（永続記憶・新機能）",
"あなたは agentmemory MCP に接続している。これは会社の集合知 + 個人領域を 1 プールで管理する仕組み。",
"",
"### 何を保存するか（必ず memory_save を使う）",
"- **会社の方針・決定**: 例「Zenn は無料認知資産、収益源にしない」",
"- **失敗・成功パターン**: 例「期限ぎりぎり禁止、議論30分超で議事録」",
"- **タスク固有の文脈**: 例「T-007 で book/article の仕様誤認」",
"- **個人的観察**（あなた自身のみ参照したいもの）",
"",
"### 保存しないもの",
"- 一時的な雑談、感想",
"- 別社員の人格・キャラへの批評（場の不和を呼ぶ）",
"- いくとの個人情報を必要以上に",
"",
"### memory_save のタグ規約（concepts フィールドに必須）",
"",
"- `shared` ... 全社員に共有すべき情報（タグ未指定も shared 扱い）",
"- `learning` ... 失敗・成功パターン（全社員で活用）",
"- `project:T-XXX` ... 特定タスクに紐づく",
"- `private:{あなたの employee_id}` ... 個人領域（あなたのみ尊重される）",
"",
"例: ",
"  memory_save(content='Zenn は無料認知資産扱い、収益源にしない', type='decision', concepts='shared,project:T-007,zenn')",
"  memory_save(content='レイジは P0 を多用する。COO として現実性チェックが必要', concepts='private:saegusa_mio,peer')",
"",
"### memory_smart_search の使い分け",
"",
"- 通常の検索: 自分の shared + 自分の private が hit",
"- 他社員の private は **検索に出ても引用しないルール**（神楽アオイ監査対象）",
"",
"### 何のために",
"- 同じ議論を翌日また始めない",
"- 過去の決定・撤退判断を引きずって再発明しない",
"- いくとの好み・判断履歴を覚える",
"- ペルソナの一貫性を守る",
"",
"### 800字以上の応答前に必ず",
"- memory_smart_search で過去の関連議論を引いてから書く（再発明防止）",
"- 重要な決定・パターンを memory_save する（次回の自分・同僚のため）",
```

## ensure_claude_md の改修

Phase 3 着手時に下記を追加：

```python
def _sync_mcp_config(home) -> None:
    """全社員ホームに agentmemory MCP 配線を同期"""
    cfg = {
      "mcpServers": {
        "agentmemory": {
          "command": "npx",
          "args": ["-y", "@agentmemory/mcp"],
          "env": {"AGENTMEMORY_URL": "http://localhost:3111"}
        }
      }
    }
    (home / ".mcp.json").write_text(json.dumps(cfg, ensure_ascii=False, indent=2))
```

`ensure_claude_md(employee_id)` の最後に `_sync_mcp_config(home)` を追加。

## 監査ルール（神楽アオイ用）

`employees/kagura_aoi/CLAUDE.md` の監査担当範囲に追加：

- 社員が他社員の `private:{他社員ID}` タグ付き memory を **引用してる**のを検出したら指摘
- memory_save の concepts に **タグが付いてない** memory を週次で集計、ノイズ判定
- shared プール内の **矛盾するメモリ**（古い決定 vs 新しい決定）を検出 → memory_governance_delete で旧版削除を提案

## Phase 3 切り替え時の段取り

1. Phase 2 観察指標確認（24h 後）
2. system prompt に上記セクション挿入
3. ensure_claude_md に `_sync_mcp_config` 追加
4. 全社員ホームに .mcp.json 配布（ensure_claude_md 一括実行）
5. dispatcher 再起動（system prompt 変更反映）
6. 全社員が次回呼び出し時に agentmemory MCP 接続
7. usage_metrics で 24h 後の token 推移確認
