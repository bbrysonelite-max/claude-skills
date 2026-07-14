# skill-miner — reference

## Batch analysis prompt

Analyze each batch directly in the main Codex agent. Delegation is optional only when the active environment permits it. Fill `{BATCH_FILE}` with
`batch1.txt` / `batch2.txt` / `batch3.txt`, and `{EXISTING}` with the current
`ls ~/.codex/skills` output plus the `built`/`declined` names from BACKLOG.md.

> You are analyzing a digest of Brent Bryson's past Codex sessions to find recurring
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

`scripts/digest_codex.py --dir ~/.codex/sessions` recursively reads current rollout JSONL. Pass each relevant project-local `.codex/sessions` directory with repeatable `--context-dir PATH` to include context-keeper Markdown snapshots; do not assume those snapshots are in the global rollout directory. The helper deduplicates candidates, then applies `--limit N` and deterministic ordering across valid rollouts and snapshots together. It keeps only user/assistant textual messages, excludes tool, reasoning, encrypted, and developer payloads, redacts credential-shaped values, and emits deterministic `digest.txt` plus optional `batchK.txt` files.

Use historical `~/.claude/projects/-Users-brentbryson/*.jsonl` only as read-only evidence with the original `scripts/digest.py`; never use that helper for current Codex rollouts.
