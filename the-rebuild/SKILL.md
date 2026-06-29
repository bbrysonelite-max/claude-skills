---
name: the-rebuild
description: Loads the full strategic context of Brent's comeback — rebuilding his NuSkin business with Tiger/AI to requalify his income, and the AI + network-marketing "tip of the sword" story that scales from it. Use when Brent says "the rebuild", "load the mission/context", "what's the plan", or when starting any work on his NuSkin requalification, the Mine / lead-gen for network marketers, the Flip the Script webinar funnel, or loading his contacts into Tiger — and any time an agent needs his goals, guardrails, and who-he-is before acting.
---

# The Rebuild — Brent's comeback mission & operating context

Load this before any work on Brent's NuSkin requalification, the Mine / lead-gen for network marketers, the Flip the Script webinar, or putting his contacts into Tiger. This is the context he is tired of re-explaining. Live links + code citations: see [REFERENCE.md](REFERENCE.md).

## The mission (the revenue anchor)
Brent is a 25-year NuSkin team lead. Sept 2025 he missed qualification → income dropped ~$60k to ~$15k. He **requalifies** (~half back, ~$30k) by building **ONE leg to 10,000 points of volume**. That number is the north star. **"Clearest path to revenue" is the lens for every decision — park pure engineering.**

## The strategy
Brent + Tiger rebuild that one leg → the rebuild becomes **THE STORY** ("I rebuilt my NuSkin business with AI") → that story raises the next round (recruits, leaders, Tiger buyers) like crazy. **AI is the "tip of the sword" NuSkin doesn't have, and Brent becomes the one who has it.** He is a 40-year warm-market master — recruiting is his deepest skill, NOT a "long game." The only NEW variable is the **prospect source** (his warm market is burned through 3 rebuilds). Sequence: **story first, then seats** — rebuild the leg; the webinar amplifies after.

## The plan (6 steps — walk ONE at a time; he's overwhelmed)
1. Export his NuSkin genealogy / warm contacts from the back office as a **CSV**.
2. **Import** that CSV into his Tiger (`/import`) — no hand-typing.
3. **Export a backup CSV** from Tiger (`/export`) and save it — insurance.
4. **Point Tiger at the goal**: re-engage these people, find builders, work toward one strong leg.
5. **Let it run + feed it** — Tiger does the follow-up he never had time for; the Mine surfaces fresh builders to add.
6. **Log the wins** — what Tiger surfaces and revives. That log IS the story.

## The audience
Active **builders / leaders**, especially from struggling companies or people looking for a better vehicle (his proven vein). **Build DEEP under one person, not wide** — depth in one leg fills 10k fastest. **Tiger's duplication is the depth engine** (recruit → give them Tiger → they go deeper). Target quality (a few real builders), not volume (a stadium).

## The two minds (do NOT confuse)
1. **Tiger's internal mind** — UNTOUCHED, read-only, finds people *in transition*. Product feature. Never re-point it.
2. **The agnostic, skill-driven Mine** (`signal-atlas` / `Datamine`, run via the `signal-mine` skill) — re-pointed per vertical. The **`network-marketers-ai`** vertical = "network marketers / people looking for automation." This is the one we aim at new prospects.

## Data safety (his #1 operator fear — answered from the code)
Leads live in **tenant-scoped Postgres** (`tenant_leads`), durable and independent of the bot — a crash / restart / pause / archive does NOT lose them. CSV `/import` + `/export` are operator tools. The ONLY thing that hard-deletes is **terminate** (drops the tenant schema). So: **keep a CSV export as insurance; use suspend, never terminate.** Product gap → add auto-backup-before-terminate BEFORE leaders load their own contacts.

## Guardrails / scars (do not repeat)
- **Don't burn leaders.** Never hand a leader their own Tiger until it is *proven* solid. Tiger is solid NOW (green health, lead engine producing) — not the old "gas chamber" builds — but green infra ≠ a guaranteed flawless leader experience.
- **Debbie is OFF the table.** Burned 4 builds ago; she's spent, a follower not an autonomous leader, lives in Spain. Base nothing on her.
- Recruiting into NuSkin is his **40-year mastery** — never frame it as the unfamiliar part.

## Working with Brent (every agent, every turn)
39-year NM vet, $30M+ earned, **warm-market specialist** — trust his domain calls. **ONE EYE**: ask ONE question at a time, keep replies short and plain. He **dictates** — noun/path typos are common; surface conflicts before saving. He's **in transition with a full head** — be a calm operator's guide, one step at a time, present-before-coding.
