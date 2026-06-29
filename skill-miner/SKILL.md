---
name: skill-miner
description: Mine Brent's past Claude Code session transcripts to surface recurring routines that should become reusable skills, deduped against what already exists, then SUGGEST the strongest new candidate(s) to Brent for a build decision. A read-only research loop — it proposes, it never auto-builds. Use when Brent says "run skill-miner", "mine my sessions", "what should be a skill", "find new skills", "auto research for skills", or on a monthly cadence via /schedule. Pairs with the BACKLOG.md ledger so each run mainly surfaces NEW routines.
---

# skill-miner

A read-only **research loop**: transcripts → recurring routines → ranked skill candidates →
a concrete **suggestion to Brent**. It proposes; building stays a separate, approved step.

## Workflow

1. **Digest** the transcripts into analyzable batches:
   `python3 scripts/digest.py --batches 3`
   Writes `digest.txt` + `batch1..3.txt` (human prompts only; skips tool-results / subagent
   noise; handles the 100MB+ files). Add `--limit N` to mine only the N most recent sessions.
2. **Establish what already exists** (the dedupe ground truth):
   `ls ~/.claude/skills` AND read this skill's `BACKLOG.md` (candidates already built/declined/proposed).
3. **Fan out 3 analyst subagents**, one per batch — each clusters routines and returns
   structured candidates. Use the prompt template in [REFERENCE.md](REFERENCE.md) (it carries
   the dedupe list + output schema). Run them in one message so they go in parallel.
4. **Synthesize** — merge the three lists, rank by frequency × TigerClaw impact, and keep only
   **genuine NEW gaps**: not covered by an existing skill, and not already `built`/`declined` in
   BACKLOG.md. Note convergence (a routine flagged by ≥2 batches is a strong signal).
5. **Update `BACKLOG.md`** — append each new candidate with status `proposed`, evidence
   (session ids), and impact. This ledger is the dedupe memory + the lightweight skill map.
6. **Suggest to Brent** (the point of the skill): present the top 1–3 new candidates as a
   concrete, actionable suggestion — name, what it'd do, how often it recurs (with evidence),
   and a one-line recommendation — and ask which (if any) to build. **One question, ranked,
   recommendation first.** Do not auto-create anything.
7. **On approval only** — invoke `write-a-skill` to build the chosen candidate, then mark it
   `built` in BACKLOG.md.

## Rules (inherits ground-truth + Brent's standing rules)

- **Read-only / proposes — never auto-builds a skill.** Suggestion + Brent's explicit go, then build.
- **No ungrounded recurrence claims.** "This recurs" must be backed by the digest (session ids /
  counts). If a routine appears once, say so — don't inflate it.
- **Dedupe hard.** Anything an existing skill or a `built` BACKLOG entry covers is not a candidate.
- **Bounded cost.** One sweep per run, ~3 analyst agents. Not an iterate-to-dry loop.

## Cadence

On-demand, or schedule a monthly pass with the `/schedule` skill. Because of BACKLOG.md, each
run mostly surfaces what's NEW since last time.

## Quick start

```bash
python3 scripts/digest.py --batches 3   # then fan out 3 analysts over batch1..3.txt (see REFERENCE.md)
```
