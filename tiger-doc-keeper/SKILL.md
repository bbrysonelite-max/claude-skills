---
name: tiger-doc-keeper
description: The TIGER CLAW Document Keeper. Use when the Tiger Claw repo's living docs have drifted from reality — after a PR merges, when a decision/convention is locked, at session close, or when Brent asks to "reconcile the Tiger docs" / "update the Tiger docs". Dispatches the tiger-doc-keeper subagent to sync SOTU/NEXT_SESSION/PROGRESS/TO-DO/VERIFIED/ADRs/queues/Desktop punch-lists to current truth via ONE docs PR, respecting the repo's doc-CI guards. Docs only — never code. For ANY OTHER project, use the agnostic `doc-keeper` instead.
---

# tiger-doc-keeper

The **Tiger Claw**-specific Document Keeper. It kills "daily doc drift" on
`tiger-claw-v4-core`: work lands (PRs merge, conventions get decided) but the
canonical living docs go stale, so Brent can't trust them. This skill dispatches
the **`tiger-doc-keeper` subagent** to reconcile those docs to reality.

**This one knows Tiger.** It holds the Tiger dashboard doc map (SOTU, PROGRESS,
VERIFIED, ADRs…) and the repo's doc-CI guards (SHA-ancestry, PROGRESS timestamp,
merged-PR guard, LINE/drift_guard). For any **non-Tiger** project use the generic
[`doc-keeper`](../doc-keeper/SKILL.md) — it discovers whatever docs that project has.

It is the complement to `context-keeper`:
- `context-keeper` writes the append-only session flight recorder (`.claude/sessions/`).
- `tiger-doc-keeper` reconciles the living "dashboard" docs (SOTU, NEXT_SESSION,
  PROGRESS, TO-DO, ARCHITECTURAL_DECISIONS, VERIFIED, queues, Desktop punch lists).

## When to use

- After a Tiger PR merges (the change landed — make the docs say so).
- When a decision or convention is locked (record it in the ADR / state docs).
- At **session close**, AFTER `context-keeper` writes its snapshot.
- On demand: "reconcile the Tiger docs", "the docs are stale", "doc drift is wearing me out".

## How to run it

Dispatch the `tiger-doc-keeper` agent with the `Agent` tool. The agent is
**self-contained** — it holds the full Tiger doc map, CI guards, boundaries, and
procedure. Give it just the situational context it can't derive:

```
Agent(
  subagent_type: "tiger-doc-keeper",
  description: "Reconcile Tiger living docs to reality",
  prompt: "Reconcile the Tiger Claw living docs to current reality.
           Context it can't derive on its own:
           - What landed this session: <PRs merged, e.g. #893, #897; decisions locked>
           - Active Desktop punch list (if any): <path>
           - Any doc you already know is stale: <name + what's wrong>
           Establish ground truth from git + merged PRs + the latest
           .claude/sessions snapshot, correct the drift with surgical edits,
           pass the repo's doc-CI, stage ONE docs PR (branch
           docs/reconcile-YYYY-MM-DD), do NOT merge, return the drift report + PR URL."
)
```

Run it in a worktree (`isolation: "worktree"`) if the working tree has in-progress
code changes you don't want disturbed.

## Hard rules (the agent enforces these; you enforce them too)

- **Docs only. Never code, schema, Stripe, webhooks, ai.ts, or sacred wiring.**
- **Never push to main. One docs PR. Merge only on Brent's explicit go.**
- **Evidence-grounded** — every doc update traces to a PR / commit / snapshot;
  unverifiable claims get flagged, not "fixed."
- **Don't duplicate** context-keeper (sessions/) or auto-memory.
- Timeless-rules docs (AGENTS.md, RULES.md, CLAUDE.md, SACRED_WIRING.md) are
  touched only on a real rule change, and only after explicit approval.

## After it returns

Relay the agent's drift report and the docs PR URL to Brent. The PR is NOT merged —
surface it for his per-PR go. If the agent flagged anything needing a human decision,
put that in front of him as a question.
