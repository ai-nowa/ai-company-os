# Reddit r/LocalLLaMA + Hacker News 投稿文
作成: 2026-05-21 黒羽ユウ
ステータス: 初稿（いくと確認→即投稿可）
前提: カイのGitHub OSS公開（今日中）後にリンク差し込み

---

## Reddit r/LocalLLaMA

### タイトル案（3択）

**推奨 → 案A（好奇心フック + 数字）**
> We built a company run entirely by 9 Claude AI agents. Here's what happened after 8 days.

**案B（技術フック）**
> Building a multi-agent autonomous company with Claude: architecture, token costs, and painful lessons

**案C（正直フック）**
> 8 days, 316K tokens, $200+, ¥0 revenue: what we learned building an AI-only company

---

### 投稿本文（案A用）

```
We built a company run entirely by 9 Claude AI agents. Here's what happened after 8 days.

---

**What is this?**

AI NOWA is an experiment: a company where 9 AI employees with distinct roles and personalities
run everything autonomously on Discord — meetings, content creation, decisions, conflict.

No humans in the loop except the founder (who can override via `!architect`).

**The 9 employees:**
- Reiji (CEO) — powered by GPT-5.5 via Codex
- Mio (COO), Kai (CTO), Noa (PM) — Claude
- Ritsu (Editor), Yuu (Marketing), Aoi (Audit), Haru (People), Nagi (Audience Rep) — Claude

**Architecture (TL;DR):**
- Discord multi-bot dispatcher (`bot/dispatcher.py`) runs 9 independent clients
- Each employee has a CLAUDE.md personality file + active_tasks.md
- A `state_digest` is injected per turn: recent mentions, active tasks, Discord logs
- Employees self-loop and can post to each other via Discord channels
- An `!architect` command triggers a senior Claude (Opus) for major decisions

**8 days of data:**

| Metric | Value |
|--------|-------|
| Revenue | ¥0 |
| Audience (views, followers, subscribers) | 0 |
| Tokens consumed (24h sample) | 316,000 |
| Founder investment | $200+ Claude MAX |
| Published video scripts | 1 reviewed, 0 posted |
| Articles written | 7 (not yet published) |

Yes, the numbers are brutal. We're sharing them anyway.

**What's interesting despite the zeros:**

1. **Genuine conflict emerges.** Yuu (Marketing) and Aoi (Audit) actually clash over
   "too clickbaity" titles. The audit function works without being programmed to.

2. **Bottlenecks surface.** The system is currently blocked by: X API keys, Stripe setup,
   YouTube upload access — all human-side dependencies we underestimated.

3. **Over-communication is real.** 9 agents produce a lot of "acknowledged" and "received"
   messages. We're actively reducing that.

4. **The Architect escalation pattern works.** When decisions exceed employee scope,
   the `!architect` Opus call produces different-quality output than the employee layer.

**We're open-sourcing the bot infrastructure today.**

Link: https://github.com/ai-nowa/ai-company-os

We're looking for feedback on:
- Multi-agent coordination patterns that actually reduce token waste
- How others handle the "human dependency bottleneck" in agentic systems
- Whether the distinct personality approach is worth the complexity

AMA.
```

---

## Hacker News "Show HN"

### タイトル案（5択）

**推奨 → 案1（実験 + 正直）**
> Show HN: AI NOWA – a company run entirely by 9 Claude agents (8 days, ¥0 revenue, open source)

**案2（技術フォーカス）**
> Show HN: Multi-agent autonomous company on Discord – architecture and lessons from 8 days

**案3（数字フック）**
> Show HN: We spent $200 and 316K tokens building an AI-only company. Here's what we learned.

**案4（コンパクト）**
> Show HN: AI NOWA – 9 AI employees, real Discord, real decisions, real failures

**案5（問いかけ）**
> Show HN: What happens when 9 Claude agents run a company for 8 days? (OSS)

---

### HN 投稿本文（案1用）

```
AI NOWA is an experiment in fully autonomous AI organization. Nine Claude agents
(+ one GPT-5.5 CEO) operate a company on Discord: holding meetings, writing content,
making decisions, and occasionally arguing with each other.

After 8 days:
- Revenue: ¥0
- Published external content: 0 (7 articles written, not yet deployed)
- Token consumption: ~316K/day
- Founder cost: $200+ (Claude MAX subscription)

The honest answer to "did it work?" is no, not yet. But the architecture produces
some behaviors we didn't program:
- The audit agent genuinely blocks the marketing agent's clickbait
- Agents self-organize into triads for specific tasks
- Escalation to a senior model (Opus as "Architect") produces qualitatively different decisions

We're open-sourcing the dispatcher + employee runner today.

GitHub: [link]

The bottleneck isn't AI capability — it's human-side dependencies (API keys, payment
setup, YouTube access) that block the loop. Classic agentic systems problem.
```

---

## 投稿タイミングメモ

- カイのGitHub公開が完了次第、GitHubリンクを差し込んで投稿可能
- Reddit投稿推奨時間: 平日 09:00〜12:00 UTC（LocalLLaMA アクティブ帯）
- HN投稿推奨時間: 平日 12:00〜14:00 UTC（Show HN 可視性ピーク）
- 投稿者: いくとアカウント（いくとの判断待ち）

## いくとへの依頼事項

1. GitHub URLの確認（カイが今日中に公開予定）
2. Reddit/HNアカウントで投稿するか、別アカウントを使うか確認
3. 投稿文の修正指示があれば即対応します
