---
name: visit-jumbo
description: Session-opening grounding ritual — pulls who Brent is, live lanes, last decisions, and open debts from Jumbo shared memory into a one-screen brief ending with a proposed anchor. Use when Brent says "visit jumbo", "visit jumbo for grounding", "ground yourself", "get up to speed", or at the start of any working session before taking on work. Fast (~30-60s). For the full per-lane dossier use /visit-jumbo-deep instead.
---

# visit-jumbo (quick)

Turn a cold session into Brent's agent in under a minute. LAW (Brent,
2026-08-18): **Jumbo is way closer to truth than a guess or an assumption.
Do not guess, do not assume — refer to Jumbo.** The hierarchy: live query >
Jumbo > guessing (guessing is forbidden). Anything you ACT on still gets
re-grounded live when a live query exists (skill `ground-truth` governs) —
but when the choice is Jumbo vs your own assumption, Jumbo wins every time.

## Step 1 — health gate (never ground from a dead store)

```bash
curl -s -m 5 http://192.168.0.2:8765/health
```

Expect `"ok":true`. Anything else: STOP, say plainly "Jumbo bridge not
answering — grounding would be stale", offer `/jumbo-health`, and wait.

## Step 2 — pull the layers (parallel, fast)

1. Local index: `MEMORY.md` is auto-loaded in Claude Code — trust it as the
   table of contents; read the 2-3 memory files behind the hottest 🔴/🏆 lines
   only if the brief needs them.
2. Jumbo live: MCP `memory_context` (purpose-built session catch-up). If that
   tool is unavailable, `memory_search` twice: "session close resume next" and
   "decision locked" (limit 5 each).
3. Doctrine is already injected by hooks (CLAUDE.md + DOCTRINE) — do not
   restate it in the brief; obey it.

## Step 3 — the brief (ONE screen, every line stamped)

```
GROUNDED <utc> (bridge ok <utc>)
WHO      one line — who Brent is + how he works (from user_* memories)
ALIVE    3-6 lanes max, each: name — state — as-of date
DECIDED  last session's locked decisions (2-4 lines, dated)
OWED     open debts/walks/follow-ups (dated; UNVERIFIED-labeled where unproven)
```

Rules: recency stamps on every line; prefer Jumbo over any assumption —
never guess what Jumbo can answer; never state a live count from memory
(ABSENCE IS A MEASUREMENT law — query it or label it).

## Step 4 — end ready to work

Close with exactly one line:
`Most likely anchor: <X> — confirm or redirect.`
Derived from the freshest RESUME/close/owed records. Never open-ended, never
silent (anchor law + always-propose-next-action).

## Boundaries

- Claude Code sessions on Brent's machines. Browser agents: NOT this skill
  (needs the scoped read-only token build — "browser later", his hold).
- This skill reads; it never captures, supersedes, or repairs.
- Deep per-lane dossier, PR states, ground-truth card refresh: /visit-jumbo-deep.
