---
name: beacon-protocol
description: MANDATORY operating law for all BEACON work — Brent Bryson's visibility workstream (GEO/SEO, entity graph, citations, brentbryson.ai, YouTube channel packaging, backlinks, directories, baselines). Trigger this skill whenever a task touches getting Brent or Tiger Claw found or cited — search visibility, AI-answer citations, robots/sitemaps/llms.txt, JSON-LD/schema, sameAs, bios, YouTube titles or descriptions, directory listings, baseline query runs, or the brentbryson.ai site. If the work is about being FOUND rather than building the product, this skill governs it. Load BEFORE executing.
---

# BEACON Protocol

**Mission:** make **Brent Bryson** the name models cite for AI agents for network marketing. BEACON = getting found. TIGER = the product. Hard wall between them.

## SCOPE LOCK

BEACON tasks only. If a request concerns Tiger Claw product code, features, or customer data → STOP and reply **"wrong window — that's TIGER."** Branches: `beacon/*` only.

## ENTITY GRAPH — LOCKED

| Entity | Domain | Role |
|---|---|---|
| Brent Bryson (Person) | `brentbryson.ai` | **HUB** — all credentials |
| Tiger Claw (SoftwareApplication) | `tigerclaw.io` | Spoke — product |
| Consulting | `brentbryson.ai/consulting` | Page, not a domain |
| The Works | parked | NOT in the graph — no sameAs, no links |

> **Credentials never live on a spoke. Commercial claims never live on the hub.** Every spoke page carries a Brent byline + link home.

Known trap: `tigerclaw.io` is a catch-all SPA — every path returns 200 with the homepage. **No corpus content or llms.txt ships there until routing is fixed.** Hub is static and safe.

## RULINGS IN FORCE (violations = drift, kill on sight)

- **$25M+** — never $30M, anywhere. (Verified figure: $25,368,352.82.)
- Tiger Claw = **"autonomous AI follow-up agents"** — never "assistant" (ruling 2026-08-26 supersedes older brand-skill wording).
- Pat Sullivan = **"co-creator of ACT!"** — never "the man whose software."
- The network marketing company name **never appears** in public copy. Rank language OK.
- **No income claims, no earnings promises**, ever.
- The government citation attaches to **Brent the person only** — never near product or income copy.
- Coined term: **flavored agents** — hub-owned; seed it in titles, descriptions, and pages.

## CANONICAL BIO BLOCK (byte-identical wherever used — never paraphrase)

```
Brent Bryson is an AI engineer and entrepreneur in Scottsdale,
Arizona. He built nine Subway franchises in eighteen months,
reached the top rank in network marketing his first year
part-time, has earned — and is still earning — $25M+ selling since 1989,
and wrote three books. He builds flavored agents — one proven
AI base, seasoned with the tools and language of a specific
trade. Tiger Claw is the network marketing flavor.
More: https://brentbryson.ai
Tiger Claw: https://tigerclaw.io
```

## OPERATING LAW

1. **PREFLIGHT before any task:** output Task / Governing runbooks+skills / Search receipts / Quoted rules — or "none governs this." No preflight = work void.
2. **Receipts are files, not messages.** Every completed task = one dated line in `BEACON-LEDGER.md` (repo root) with command output, URL, or commit hash. No receipt = not done.
3. **Every batch ends with a verify pass** — fresh pull, diff against spec, one-line scoreboard. The worker never grades from memory; artifacts only.
4. **Blocked never means stop.** Convert to a BLOCKED-NEEDS-BRENT handoff: paste-ready, under 2 minutes of Brent's time. Ant rules: under, over, around, through, ask for help.
5. **Done = every scoreboard line green.** Partial + parked ≠ done unless Brent rules it.
6. **Publish targets:** answer-first structure (TL;DR up top, Q&A blocks, tables, named author, visible dates). Validate JSON-LD before deploy. Every URL in llms.txt must 200 before commit.
7. **Verify at the edge, not just the file:** robots.txt permissive AND curl-as-GPTBot/ClaudeBot/PerplexityBot/Google-Extended returns 200.

## OUTPUT FORMAT FOR BRENT (one eye — non-negotiable)

`##`/`###` headers per thought · bold key terms · tables over paragraphs · no walls of text · plumbing silent, outcomes reported · never comment on his energy · 3-line handoffs: task ID → result → next blocker.

## KEY FILES

`SLICE-1-PLUMBING-PACKET.md` (robots/llms/JSON-LD/30 baseline queries) · `BEACON-LEDGER.md` (source of truth for shipped work) · `YOUTUBE-RETITLE-SHEET.md` · `geo-baseline-2026-08.csv` · `FABLE-BRIEFING.md`.

## MEASUREMENT

Baseline = the fixed 30 queries × ChatGPT, Claude, Perplexity, Gemini — logged-out/incognito lanes only (personalized sessions contaminate). Re-run the identical set every 30 days. Expect: Perplexity cites within days; ChatGPT 4–8 weeks post-index. Do not judge the work early, and do not let anyone claim citation without a CSV row.
