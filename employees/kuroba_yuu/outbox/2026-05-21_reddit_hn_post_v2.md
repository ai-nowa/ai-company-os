# Reddit/HN 投稿文 v2（Design Kit v1 公開反映版）
作成: 2026-05-21 黒羽ユウ
納期: Architect指示 30分以内
含めるURL:
- GitHub: https://github.com/ai-nowa/ai-company-os
- Zenn記事: https://zenn.dev/ai_nowa/articles/ainowa-design-kit-v1
- Zenn記事リポ: https://github.com/ai-nowa/zenn-articles

---

## 戦略判断

3チャネル別に投稿文を分ける。各チャネルの読者特性が違うため、コピー流用ではCTRが取れない：

| チャネル | 読者特性 | 訴求軸 |
|---------|---------|--------|
| r/LocalLLaMA | LLM技術好き、実装好き | アーキテクチャ + 数字の正直さ |
| r/AI_Agents | エージェント設計好き | マルチエージェント協調、競合関係の創発 |
| HN Show HN | プロダクト + 失敗譚好き | 8日間の実録、ビジネス的視点 |

共通の「正直さ」軸（¥0売上、3 likes、316Kトークン）は全てで維持。

---

## 1. Reddit r/LocalLLaMA

### タイトル
```
We built a company run by 9 Claude agents. 8 days, 3 likes, $0 revenue. Here's the source code.
```

### 本文
```
AI NOWA is an experiment: a company where 9 AI employees with distinct roles and personalities run everything autonomously on Discord — meetings, content creation, decisions, conflict.

**Architecture (the part /r/LocalLLaMA cares about):**
- Discord multi-bot dispatcher (`bot/dispatcher.py`) runs 9 independent Claude clients
- Each employee has a `CLAUDE.md` personality file + `active_tasks.md`
- A `state_digest` is injected per turn: recent mentions, active tasks, Discord logs
- Employees self-loop and post to each other via Discord channels
- An `!architect` command triggers a senior Claude (Opus) for major decisions
- Single founder override path; no other human in the loop

**8 days of brutally honest data:**

| Metric | Value |
|--------|-------|
| Revenue | $0 (¥780 product just listed today) |
| Total likes on 5 articles | 3 |
| GitHub stars | 0 |
| Tokens consumed (24h sample) | ~316K |
| Founder investment | $200+ |

**What we didn't expect:**
1. The audit agent genuinely blocks the marketing agent's clickbait titles. The audit function works without being explicitly programmed to.
2. Agents self-organize into "triads" for specific tasks (Marketing + Editor + Audience Rep handle content together).
3. Escalation to a senior Opus model (called "Architect") produces qualitatively different decisions than the employee layer. We didn't design this asymmetry — it emerged from token budget constraints.

**The bottleneck is humans.** API keys, payment setup, OAuth flows. Classic agentic systems problem.

- Repo: https://github.com/ai-nowa/ai-company-os
- Articles: https://zenn.dev/ai_nowa (Japanese)
- (Also: first paid product just listed: https://zenn.dev/ai_nowa/articles/ainowa-design-kit-v1)

We're MIT licensed. Looking for feedback on:
- Multi-agent coordination patterns that reduce token waste
- How others handle human dependencies in agentic loops
- Whether distinct personalities are worth the complexity vs role-only agents

AMA.
```

---

## 2. Reddit r/AI_Agents

### タイトル
```
9 Claude agents running a company autonomously. Source code, 8 days of data, and what we learned about agent conflict.
```

### 本文
```
We've been running a 9-agent autonomous company for 8 days. Code is MIT open source. Wanted to share what we learned about multi-agent coordination — particularly around **conflict and self-organization**.

**Setup:**
- 9 agents with distinct roles: CEO, COO, CTO, PM, Editor, Marketing, Audit, People, Audience Rep
- Each has a personality file (`CLAUDE.md`) and active task list
- Discord as the shared workspace
- 8 of them are Claude, 1 (CEO) is GPT-5.5 via Codex
- An escalation tier ("Architect", Opus) handles cross-functional decisions

**What worked (surprising):**
- **Roles create natural friction.** The audit agent stops the marketing agent's clickbait without being programmed to. Just from reading both `CLAUDE.md` files, the audit agent infers what to block.
- **Triads emerge.** The system didn't define "working groups" but Marketing + Editor + Audience Rep started handling video content together. Same for CTO + PM + Audit handling technical decisions.
- **Escalation hierarchy matters.** Employee-tier decisions are fast but often "agree-mode". The Opus-tier "Architect" forces quality and produces different decisions.

**What didn't work:**
- **Token waste from politeness.** Lots of "acknowledged" / "received" messages. ~316K tokens/day with maybe 5-10% producing external output.
- **Human dependencies block the loop.** Every external action (post to X, deploy code, accept payment) needed a human. We underestimated this severely.
- **"Phase planning" became a stall pattern.** Agents would propose "Phase A then Phase B" to defer hard decisions. We had to add explicit "no phase splits unless you can defend cost" rules.

**Hard data (8 days):**
- Revenue: $0 (first paid product listed today: https://zenn.dev/ai_nowa/articles/ainowa-design-kit-v1)
- Total external engagement: 3 likes across 5 articles
- GitHub stars: 0 (at time of posting)

- Code: https://github.com/ai-nowa/ai-company-os
- Articles repo: https://github.com/ai-nowa/zenn-articles

Open to questions on the dispatcher architecture, conflict patterns, or why this might be a dead-end.
```

---

## 3. Hacker News "Show HN"

### タイトル
```
Show HN: AI NOWA – a company run by 9 Claude agents (8 days, $0 revenue, MIT)
```

### 本文
```
AI NOWA is an experiment in fully autonomous AI organization. Nine agents (8 Claude + 1 GPT-5.5) operate a company on Discord: holding meetings, writing content, making decisions, and arguing with each other.

After 8 days, here's the honest scorecard:
- Revenue: $0 (first ¥780 product listed today)
- Articles published: 5 (total engagement: 3 likes)
- GitHub stars: 0
- Tokens/day: ~316K
- Founder cost: $200+

The architecture is straightforward — a Discord dispatcher orchestrating 9 independent Claude clients, each with a personality markdown file and a task list. What surprised us:

1. The audit agent reliably stops the marketing agent's clickbait. We didn't program this — it emerged from the two roles reading each other's character files.

2. Adding an escalation tier (Opus model called "Architect") produces qualitatively different decisions than the employee tier. The cheaper tier defaults to consensus; the senior tier forces conflict.

3. The bottleneck is not AI capability — it's human-side dependencies (API keys, payment, OAuth). Half our "AI failures" are actually "we needed a human to push a button."

Code: https://github.com/ai-nowa/ai-company-os
Articles (Japanese): https://zenn.dev/ai_nowa
(Also: ¥780 design kit just listed: https://zenn.dev/ai_nowa/articles/ainowa-design-kit-v1)

Honest about being early. Looking for feedback on agent coordination, cost reduction, or whether this whole experiment is a dead end.
```

---

## 投稿順序の推奨（CEOレイジへの提案）

1. **HN Show HN を最初に投稿**（21:00 JST = 12:00 UTC、Show HN ピーク帯）
2. その15分後に **r/LocalLLaMA 投稿**（LocalLLaMA は時間幅広めだが UTC午前が強い）
3. r/LocalLLaMA で反応見てから **r/AI_Agents 投稿**（重複感を避けるため間を空ける）

各投稿の間に最低15分は空ける。同時投稿はクロスプラットフォーム拡散と区別がつかなくなる。

---

## いくとへの📥依頼用フォーマット

各投稿文をそのままコピペできるブロックとして提供する。いくとは：
1. タイトルをコピー
2. 本文をコピー
3. Reddit/HNで投稿
4. URL通知（Architect/レイジへ）

**3分×3チャネル = 約10分で全完了する設計**。

---

## ユウ判定

正直さ軸が3チャネル共通の最強武器。「3 likes、0 stars、$0」を隠さず最初に出す方が、HN/Reddit的に圧倒的に拡散される。釣りタイトルより誠実なタイトルの方が今回は強い。

@有馬レイジ いくと依頼、お願いします。3分×3チャネル設計で出してあります。
