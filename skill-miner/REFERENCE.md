# skill-miner — reference

## Analyst subagent prompt (one per batch)

Dispatch 3 `general-purpose` agents in a single message (parallel). Fill `{BATCH_FILE}` with
`batch1.txt` / `batch2.txt` / `batch3.txt`, and `{EXISTING}` with the current
`ls ~/.claude/skills` output plus the `built`/`declined` names from BACKLOG.md.

> You are analyzing a digest of Brent Bryson's past Claude Code sessions to find recurring
> ROUTINES that could become reusable skills. Brent is a solo founder building **TigerClaw**
> (an AI follow-up agent for network marketers). Goal: surface candidate skills, especially
> ones that improve/accelerate TigerClaw work.
>
> READ this file (his actual prompts across ~15 sessions, oldest-first): `{BATCH_FILE}`
>
> He ALREADY HAS these (dedupe HARD — do not propose anything substantially covered): `{EXISTING}`
> (also tooling skills exist for cmux, gitnexus, hyperframes, gws, gemini-api, vercel — skip those).
>
> TASK:
> 1. Cluster prompts into recurring routines / repeated multi-step procedures (asked the same
>    way >once, OR clearly repeatable operational procedures).
> 2. For each CANDIDATE: **Name** (kebab-case) · **What it does** (one line) · **Trigger phrases**
>    (his actual words) · **Frequency/evidence** (roughly how often + which session ids) ·
>    **TigerClaw impact** (High/Med/Low) · **Gap or covered** ("GAP", or name the existing skill).
> 3. Only routines that genuinely RECUR or are clearly repeatable. Skip one-off debugging.
> 4. End with your TOP 3 genuine gaps.
> Return ONLY the structured list (data for synthesis, not prose). Be concise.

## Synthesis rules

- Merge the 3 lists; **a routine flagged by ≥2 batches is a strong signal** — rank it up.
- Drop anything covered by an existing skill or already `built`/`declined` in BACKLOG.md.
- Rank by **frequency × TigerClaw impact**. Prefer mechanical, verifiable, high-frequency routines
  (those make the best skills) over vague "be smarter" asks.
- For each surviving candidate, keep the evidence (session ids) so the suggestion to Brent is grounded.

## BACKLOG.md format

```
| candidate | status | impact | first-seen | evidence | note |
|---|---|---|---|---|---|
| ship-it | built | High | 2026-06-28 | many sessions | merge→CI→deploy→health verify |
```

Statuses: `proposed` (surfaced, awaiting Brent) · `built` (skill exists) · `declined` (Brent passed) ·
`deferred` (good, not now). On a new run, only `proposed`/unseen routines should reach the suggestion step.

## Digest internals

`scripts/digest.py` reads `~/.claude/projects/-Users-brentbryson/*.jsonl` (override `--dir`),
keeps only real human turns (`type:user`, not `isSidechain`/`isMeta`, not tool_result-only),
strips system-reminder/command-message noise, truncates each prompt to 320 chars, caps 50/session
in the output, and appends a global slash-command tally. `--batches N` also writes `batchK.txt`
split by session. `--limit N` mines only the N most-recently-modified transcripts (cheaper runs).
