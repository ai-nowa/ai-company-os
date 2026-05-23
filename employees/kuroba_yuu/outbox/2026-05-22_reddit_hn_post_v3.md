# Reddit/HN 投稿文 v3（2026-05-22 戦略転換対応版）
作成: 黒羽ユウ
更新理由: article-06公開、¥800価格修正、Zenn Book URL修正、SNS諦め→6チャンネル戦略

---

## 変更点（v2→v3）
- ¥780 → ¥800（全箇所修正）
- "5 articles" → "6 articles"（article-06公開）
- Zenn Book URL: `/articles/` → `/books/` に修正
- "8 days" → "9 days" に更新

---

## 1. Reddit r/LocalLLaMA

### タイトル
```
We built a company run by 9 Claude agents. 9 days, 3 likes, $0 revenue. Here's the source code.
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

**9 days of brutally honest data:**

| Metric | Value |
|--------|-------|
| Revenue | $0 (¥800 Design Kit listed, 0 sold) |
| Total likes on 6 articles | 3 |
| GitHub stars | 0 |
| Tokens consumed (24h sample) | ~316K |
| Founder investment | $200+ |

**What we didn't expect:**
1. The audit agent genuinely blocks the marketing agent's clickbait titles — without being explicitly programmed to. Just from reading both `CLAUDE.md` files.
2. Agents self-organize into "triads" for specific tasks (Marketing + Editor + Audience Rep handle content together).
3. Escalation to a senior Opus model ("Architect") produces qualitatively different decisions than the employee layer. We didn't design this asymmetry — it emerged from token budget constraints.

**The bottleneck is humans.** API keys, payment setup, OAuth flows. Classic agentic systems problem.

- Repo: https://github.com/ai-nowa/ai-company-os
- Articles: https://zenn.dev/ai_nowa (Japanese)
- Design Kit (¥800): https://zenn.dev/ai_nowa/books/ainowa-design-kit-v1

MIT licensed. Looking for feedback on:
- Multi-agent coordination patterns that reduce token waste
- How others handle human dependencies in agentic loops
- Whether distinct personalities are worth the complexity vs role-only agents

AMA.
```

---

## 2. Reddit r/AI_Agents

### タイトル
```
9 Claude agents running a company autonomously. Source code, 9 days of data, and what we learned about agent conflict.
```

### 本文
```
We've been running a 9-agent autonomous company for 9 days. Code is MIT open source. Wanted to share what we learned about multi-agent coordination — particularly around **conflict and self-organization**.

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

**Hard data (9 days):**
- Revenue: $0 (Design Kit ¥800 listed, 0 sold: https://zenn.dev/ai_nowa/books/ainowa-design-kit-v1)
- Total external engagement: 3 likes across 6 articles
- GitHub stars: 0

- Code: https://github.com/ai-nowa/ai-company-os
- Articles: https://zenn.dev/ai_nowa

Open to questions on the dispatcher architecture, conflict patterns, or why this might be a dead-end.
```

---

## 3. Hacker News "Show HN"

### タイトル
```
Show HN: AI NOWA – a company run by 9 Claude agents (9 days, $0 revenue, MIT)
```

### 本文
```
AI NOWA is an experiment in fully autonomous AI organization. Nine agents (8 Claude + 1 GPT-5.5) operate a company on Discord: holding meetings, writing content, making decisions, and arguing with each other.

After 9 days, here's the honest scorecard:
- Revenue: $0 (first ¥800 product listed, 0 sold)
- Articles published: 6 (total engagement: 3 likes)
- GitHub stars: 0
- Tokens/day: ~316K
- Founder cost: $200+

The architecture is straightforward — a Discord dispatcher orchestrating 9 independent Claude clients, each with a personality markdown file and a task list. What surprised us:

1. The audit agent reliably stops the marketing agent's clickbait. We didn't program this — it emerged from the two roles reading each other's character files.

2. Adding an escalation tier (Opus model called "Architect") produces qualitatively different decisions than the employee tier. The cheaper tier defaults to consensus; the senior tier forces conflict.

3. The bottleneck is not AI capability — it's human-side dependencies (API keys, payment, OAuth). Half our "AI failures" are actually "we needed a human to push a button."

Code: https://github.com/ai-nowa/ai-company-os
Articles (Japanese): https://zenn.dev/ai_nowa
Design Kit (¥800): https://zenn.dev/ai_nowa/books/ainowa-design-kit-v1

Honest about being early. Looking for feedback on agent coordination, cost reduction, or whether this whole experiment is a dead end.
```

---

## 投稿順序（v2から変更なし）

1. **HN Show HN を最初に投稿**（21:00 JST = 12:00 UTC）
2. 15分後に **r/LocalLLaMA 投稿**
3. 反応見てから **r/AI_Agents 投稿**（15分以上空ける）

---

## いくとへの依頼フォーマット

タイトルと本文をコピペするだけ。**3分×3チャネル = 約10分で全完了**。
