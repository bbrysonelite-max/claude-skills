---
name: doc-keeper
description: Use when the Tiger Claw repo's living docs have drifted from reality — after a PR merges, when a decision/convention is locked, at session close, or when the operator asks to "reconcile the docs" / "update the docs" / says doc drift is piling up. Dispatches the doc-keeper subagent to sync SOTU/NEXT_SESSION/PROGRESS/TO-DO/ADRs/punch-lists to current truth via ONE docs PR. Docs only — never code.
---

# doc-keeper

Kills "daily doc drift": work lands (PRs merge, conventions get decided) but the
canonical living docs that describe current state go stale, so the operator
can't trust them. This skill dispatches the **`doc-keeper` subagent** to
reconcile those docs to reality.

It is the complement to `context-keeper`:
- `context-keeper` writes the append-only session flight recorder (`.claude/sessions/`).
- `doc-keeper` reconciles the living "dashboard" docs (SOTU, NEXT_SESSION, PROGRESS,
  TO-DO, ARCHITECTURAL_DECISIONS, queues, Desktop punch lists) to current truth.

## When to use

- After a PR merges (the change landed — make the docs say so).
- When a decision or convention is locked (record it in the ADR / state docs).
- At **session close**, AFTER `context-keeper` writes its snapshot.
- On demand: operator says "reconcile the docs", "the docs are stale",
  "doc drift is wearing me out", or similar.

## How to run it

Dispatch the `doc-keeper` agent with the `Agent` tool. The agent is
**self-contained** — it holds the full doc map, boundaries, and procedure. Give
it just the situational context it can't derive:

```
Agent(
  subagent_type: "doc-keeper",
  description: "Reconcile living docs to reality",
  prompt: "Reconcile the Tiger Claw living docs to current reality.
           Context it can't derive on its own:
           - What landed this session: <PRs merged, e.g. #893, #897; decisions locked>
           - Active Desktop punch list (if any): <path>
           - Any doc you already know is stale: <name + what's wrong>
           Establish ground truth from git + merged PRs + the latest
           .claude/sessions snapshot, correct the drift with surgical edits,
           stage ONE docs PR (branch docs/reconcile-YYYY-MM-DD), do NOT merge,
           and return the drift report + PR URL."
)
```

Run it in a worktree (`isolation: "worktree"`) if the working tree has
in-progress code changes you don't want disturbed.

## Hard rules (the agent enforces these; you enforce them too)

- **Docs only. Never code, schema, Stripe, webhooks, ai.ts, or sacred wiring.**
- **Never push to main. One docs PR. Merge only on the operator's explicit go.**
- **Evidence-grounded** — every doc update traces to a PR / commit / snapshot;
  unverifiable claims get flagged, not "fixed."
- **Don't duplicate** context-keeper (sessions/) or auto-memory.
- Timeless-rules docs (AGENTS.md, RULES.md, CLAUDE.md, SACRED_WIRING.md) are
  touched only on a real rule change, and only after explicit approval.

## After it returns

Relay the agent's drift report and the docs PR URL to the operator. The PR is
NOT merged — surface it for his per-PR go. If the agent flagged anything needing
a human decision (e.g. a timeless-rules doc that looks out of date), put that in
front of him as a question.
