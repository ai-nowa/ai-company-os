# いくとへの依頼: Zenn 記事 PV 数の共有（1回のみ）

依頼者: 三枝ミオ（COO） / 起票: ユウ依頼受け
作成日: 2026-05-18
依頼先: 📥｜いくと依頼
優先度: P1
関連タスク: T-030

---

## お願い（5分以内）

Zenn ダッシュボードで以下の2記事の PV 数を確認し、`company/metrics.csv` に追記してください。

### 対象記事

| スラッグ | 記事タイトル | 追記キー |
|---------|------------|---------|
| `ai-nowa-design-record-v01` | AI NOWA 設計記録 v0.1 | `zenn,article_v0.1_pv` |
| `ai-nowa-design-record-v02` | AI NOWA 設計記録 v0.2 | `zenn,article_v0.2_pv` |

### 手順

1. https://zenn.dev にログイン（ai-nowa アカウント）
2. ダッシュボード → 「記事」→ 各記事の PV 数を確認
3. `company/metrics.csv` の PENDING 行を実数に書き換え:

```
2026-05-18T__:__:__+09:00,zenn,article_v0.1_pv,【PV数】,count,いくと手動取得
2026-05-18T__:__:__+09:00,zenn,article_v0.2_pv,【PV数】,count,いくと手動取得
```

### 完了後

📥｜いくと依頼 に「Zenn PV追記完了」と返信してください。  
完了確認後、ユウが T-030 Phase 1（週次モニタリング）に移行します。

---

*起票: 三枝ミオ（COO）/ 2026-05-18*
