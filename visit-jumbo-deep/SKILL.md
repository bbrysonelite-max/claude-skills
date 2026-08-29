---
name: visit-jumbo-deep
description: Deep grounding dossier — chains /visit-jumbo's quick brief first, then drills per-lane Jumbo queries, repo/PR states, and a full health verdict into a working dossier. Use when Brent says "visit jumbo deep", "deep grounding", "full dossier", "ground yourself deep", after a long gap between sessions, or before taking on a consequential build. Slower (several minutes). For a fast session start use /visit-jumbo.
---

# visit-jumbo-deep

CHAIN: Stage 1 IS the `/visit-jumbo` skill — execute it in full (health gate →
layers → one-screen brief). Then extend. Same laws: Jumbo beats guessing —
never guess or assume what Jumbo can answer (Brent 2026-08-18); every line
stamped; live re-ground before acting where a live query exists.

## Stage 2 — drill each ALIVE lane (from Stage 1's brief)

For each lane (cap 6):
1. `memory_search` the lane by name + "decision OR owed OR blocked" (limit 5).
2. If the lane has a repo (MEMORY.md names it): `git -C <repo> log --oneline -3`
   + `gh pr list --repo <owner/repo> --limit 5` — real PR states, not remembered
   ones.
3. One paragraph per lane: state, last receipt (UTC), open items, contradictions
   between memory and repo (repo wins; flag the drift).

## Stage 3 — system truth floor

1. Full `/jumbo-health` pass (its 4-step verdict block, receipts).
2. Ground-truth cards: if a Tiger lane is alive, run
   `bash ~/.claude/hooks/ground-truth-card.sh --refresh` and quote the fresh
   card — never cite its numbers from memory.
3. Scheduled-jobs pulse: latest lines of `~/Library/Logs/memory-check.log` and
   `memory-sweep.log`; PROPOSALS.md pending-row count if a sweep has run.

## Stage 4 — the dossier

```
DOSSIER <utc>  (jumbo GO|RED, cards fresh <utc>)
WHO + HOW      2-3 lines
LANES          per-lane paragraphs from Stage 2 (receipts inline)
DRIFT          every memory-vs-repo contradiction found (or "none found")
OWED           consolidated, dated, UNVERIFIED-labeled where unproven
RISKS          top 2-3 from tonight's state (grounded only — no generic filler)
```

Close with exactly one line:
`Most likely anchor: <X> — confirm or redirect.`

## Boundaries

- Everything read-only; no captures/supersedes/repairs/deploys.
- If Stage 1's health gate fails, STOP there — a deep dossier from a sick
  store is confident garbage.
- Claude Code sessions only (browser agents wait on the scoped-token build).
