# agentmemory 導入設計

**Status**: ❌ **撤退（2026-05-18 朝）**
**Owner**: Architect (Claude / Opus)
**関連タスク**: #70

## 撤退理由（2026-05-18 朝・いくと判断）

設計詰めの最中、いくとから本質的な指摘を受けて再検討した結果、撤退を決定。

### 撤退ポイント

1. **当初目的（token 削減）が達成困難**
   - agentmemory の `memory_smart_search` は project/scope フィルタを持たない
   - 「private タグで個人領域」運用も「context に与えて無視する」は AI に不可能
   - 結果として token 削減効果は限定的

2. **完全分離は重い実装が必須**
   - 9 instance（HOME 偽装、リソース 9倍 + onboarding 詰まり）
   - MCP wrapper（1日仕事）
   - 既存仕組み（state_digest 改善）で同等効果を狙う方がコスパ良い

3. **AI NOWA 固有の要件と設計が合わない**
   - agentmemory は「個人開発者 + multi AI ツール（Claude Code / Cursor / Codex 等）」想定
   - AI NOWA は「異なるペルソナの 9 社員」運用
   - 公式機能で multi-agent ペルソナ分離をサポートしていない

## 学び（次回への教訓）

- ❗ **大きい依存（外部サービス・MCP）を入れる前に「既存仕組みで何ができるか」をまず確認すべき**
- ❗ **「auto-capture が魅力的」という見栄えに引っ張られた**。AI NOWA 固有要件（multi-agent ペルソナ分離）の検証が後回しになった
- ❗ **設計判断の誤り**: 前提（token 削減目的）と仕様（分離機能の有無）を最初に突き合わせるべきだった

## 代替対応（既存仕組みの改善）

1. **`state_digest` のさらなる絞り込み**: 必要な情報だけ context に流す
2. **「議論ループ検知」の強化**: 同一トピック 30回出現で alert（既に dynamic_config で実装済、閾値見直し）
3. **`shared/decisions/` `shared/docs/` の整備徹底**: 「過去判断は grep で引ける」状態を維持
4. **`claude_session_id` resume の効果計測**: 既に動いてる仕組みの定量評価

これらを別タスクとして COO と詰める。

## 撤退で実施した作業

- `npm uninstall -g --prefix ~/.local @agentmemory/agentmemory` は未実行（パッケージは残してある、再検討時に使える）
- `~/.agentmemory/` ディレクトリは残置（参考データとして保持）
- `~/.claude.json` の agentmemory 行は事前削除済
- mio の `.mcp.json` 削除済
- agentmemory プロセス停止済（port 3111/3113/3112/49134 全部 listening なし確認）
- mio・aoi・reiji に Phase 2 中断・撤退通知（📢、`label: agentmemory_phase2_aborted`）

---

# 以下、参考のため当初設計を保持（非アクティブ）

## 採用理由

| | 値 |
|---|---|
| LongMemEval-S R@5 | **95.2%**（業界トップ） |
| token/session | **~1.9K**（既存 CLAUDE.md 22K+ → 92%削減） |
| 外部 DB | **0**（SQLite ローカル完結） |
| MCP tools | **51 個** |
| マルチエージェント | **公式設計**（1 サーバー shared） |
| Claude Code 統合 | **ネイティブプラグイン**（12 hooks） |

AI NOWA の 9社員 + Architect が **同じメモリサーバーを共有**できる構造。CLAUDE.md replace の哲学が私たちと一致。

## 設計決定（いくと判断 2026-05-17 夜）

### D-1. 既存 `employees/{emp}/memory/` の扱い
- **凍結（read-only 参照のみ）**
- 今後の記憶は agentmemory にのみ保存
- 既存 facts.md / decisions.md / learnings.md はノイズ持ち込まないため import しない
- クリーンスタートを優先

### D-2. テスト社員（Phase 2）
- **三枝ミオ（COO）** 1名で1日テスト
- 理由：議論ループ最多、整理役、効果が一番見えやすい

### D-3. Phase 2 期間
- **1日テスト**（スピード重視）
- 1日後に指標確認 → Phase 3 全員展開 or 設定調整

## Phase 設計

### Phase 1: サーバー起動 + 全社員 MCP 配線（1-2時間・実装は明日以降）

```bash
# 1. インストール（社員権限の流儀に沿って ~/.local 配下）
npm install -g --prefix ~/.local @agentmemory/agentmemory

# 2. サーバー起動テスト
~/.local/bin/agentmemory  # :3111 + :3113

# 3. Claude Code 連携
~/.local/bin/agentmemory connect claude-code

# 4. demo で動作確認
~/.local/bin/agentmemory demo

# 5. ヘルスチェック
curl http://localhost:3111/agentmemory/health
```

#### Phase 1 タスク
- [ ] npm install と動作確認
- [ ] `bot/watchdog.py` に agentmemory プロセス監視を追加（落ちたら再起動）
- [ ] 起動順序：agentmemory → dispatcher（systemd-like）
- [ ] 各社員ホーム `.mcp.json` に agentmemory MCP stdio を追加
- [ ] `employee_runner._exec_claude` の起動コマンドが MCP 接続を確実にハンドル

### Phase 2: 三枝ミオ 1名で1日テスト

#### 設定
- mio の `.mcp.json` だけ agentmemory MCP 有効化
- 他8社員 + Architect は従来通り

#### 観察指標（24時間運用後に判定）
| 指標 | 現状 | Phase 2 目標 |
|------|------|-------------|
| mio の token/session | 平均 ~10K字 | **8K字以下**（agentmemory 効果実証） |
| mio が同じ議論を繰り返す回数 | (要ベースライン取得) | **半減** |
| mio の `memory_save` 呼び出し成功 | 0 | **10+ 件/日** |
| MCP 接続失敗・エラー | 0 | **0 維持** |

#### 撤退基準
- agentmemory MCP が **30分連続で接続失敗**
- mio の token 消費が**逆に増える**（移行コスト超過）
- mio の応答品質が**悪化**（人格ブレ、矛盾発言）

### Phase 3: 9社員 + Architect 全員展開

#### 条件
Phase 2 で「token 削減 + 議論ループ半減 + エラーなし」が確認されたら即実行。

#### 作業
- `ensure_claude_md()` 拡張：`.mcp.json` を全社員に auto-sync（subagent と同じパターン）
- 既存の `context_assembler.state_digest` を段階縮小：agentmemory の auto-inject と二重 context にしない
- usage_metrics で全社員の token 推移を継続観察

## 想定アーキテクチャ

```
┌────────────────────────────────────────────────┐
│ AI NOWA host                                   │
│                                                │
│  ┌──────────────────────────┐                  │
│  │ agentmemory server       │  port 3111       │
│  │  - SQLite store          │  ← 全 MCP client │
│  │  - iii-engine            │   が共有         │
│  │  - 51 MCP tools          │                  │
│  └────────┬─────────────────┘                  │
│           │                                    │
│  ┌────────┴─────────────────┐                  │
│  │ viewer (web UI)          │  port 3113       │
│  └──────────────────────────┘                  │
│                                                │
│  ┌──────────────────────────┐                  │
│  │ bot/watchdog.py          │ → agentmemory    │
│  │                          │   と dispatcher  │
│  │                          │   両方監視       │
│  └──────────────────────────┘                  │
│                                                │
│  ┌──────────────────────────┐                  │
│  │ bot/dispatcher.py        │                  │
│  │   ↓ spawns               │                  │
│  │ claude code subprocesses │ ─MCP─→ :3111     │
│  │   (各社員 + Architect)   │                  │
│  └──────────────────────────┘                  │
└────────────────────────────────────────────────┘
```

## 残設計事項（実装時に詰める）

### 並走中の context 二重化
agentmemory の auto-inject と現行 `state_digest` の重複をどう減らすか。
- 案: state_digest から「自分宛メンション」「直近 Discord ログ」を削除、agentmemory に任せる
- 案: agentmemory を補助的に使い、state_digest は維持

### 9社員の memory 区分（2026-05-18 朝・いくと確定）

**確定方針**: **1プール共有 + `private` タグで個人領域**

調査結果：
- agentmemory の `memory_smart_search` は **project/scope フィルタ無し** = デフォルト global search
- 完全分離するには 9 instance（重い）or wrapper（中コスト）必要
- ユーザー判断：個人・共有 両方認める、タグで運用分離

#### 運用ルール（Phase 3 展開時に system prompt に明記）

**memory_save の `concepts` フィールドにタグを必須化：**

| タグ | 内容 | 例 |
|------|------|-----|
| `shared` | 全社員が見るべき情報 | 会社の方針、決定、撤退判断 |
| `learning` | 失敗・成功パターン（全社員で活用） | 「議論30分超で議事録」「期限ぎりぎり禁止」 |
| `project:T-XXX` | 特定タスクに紐づく | `project:T-007` |
| **`private:{employee_id}`** | **個人領域**（その社員のみ尊重） | `private:saegusa_mio`（mio が自分の観察記録） |

**ルール**：
- 「会社の決定・パターン」→ `concepts: "shared,..."` で保存（タグなしも shared 扱い）
- 「個人的観察・感情・他社員のキャラ観察」→ `concepts: "private:{自分のID},..."` で保存
- 他社員は他人の `private:` タグ付き memory を **検索結果に出ても引用しないルール**（神楽アオイ監査対象）

#### 検索の使い分け

- **通常検索** (`memory_smart_search`)：全体プール検索、shared + 自分の private が hit
- **個人領域参照** (`memory_facet_query`)：自分の `private:{自分のID}` だけ絞り込み

#### Architect の活用

- Architect observer ループは `memory_smart_search` で **shared メモリのみ** 検索
- 「過去の似た議論」「過去の同種失敗」を検出して介入
- 個人 private memory は触らない（プライバシー的に）

### Codex の扱い
- レイジは Codex CLI (gpt-5.5) で動く
- agentmemory は Codex CLI もサポート（README に明記）
- ただし MCP 配線方式が claude code と異なる
- Phase 3 で対応、Phase 2 では mio のみ（Claude Code）に絞ることで回避

### memory への保存フィルタリング
- 12 hooks 全 ON で観察、ノイズ多ければ間引く
- agentmemory の 4-tier consolidation + decay でノイズは自動圧縮される設計
- まずデフォルト設定で運用、調整は実測ベース

## 公式リンク
- GitHub: https://github.com/rohitg00/agentmemory
- ランディング: https://agent-memory.dev
- npm: https://www.npmjs.com/package/@agentmemory/agentmemory
- ベンチマーク: `benchmark/LONGMEMEVAL.md`, `benchmark/COMPARISON.md`

## 次回開始時のチェックリスト

明朝 Architect が観察ループで状態確認した後、Phase 1 着手：

1. `npm install -g --prefix ~/.local @agentmemory/agentmemory`
2. `~/.local/bin/agentmemory --version` 確認
3. `agentmemory demo` で動作確認
4. watchdog 統合（agentmemory 監視追加）
5. mio の `.mcp.json` 設定
6. テスト：mio に「Architect から1問」発火 → memory_save が走るか確認
7. Phase 2 開始：1日観察
