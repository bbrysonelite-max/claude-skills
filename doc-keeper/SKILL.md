---
name: doc-keeper
description: The project-agnostic Document Keeper. Use on ANY project when its living/dashboard docs have drifted from reality — after a PR merges, when a decision/convention is locked, at session close (after context-keeper), or when the user says "reconcile the docs" / "update the docs" / "the docs are stale". Dispatches the doc-keeper subagent, which DISCOVERS whatever living docs the project actually has (README, CHANGELOG, status/handoff docs, ADRs, docs/, a domain index, punch-lists) and reconciles them to current truth via ONE docs PR on the repo's default branch. Docs only — never code; never merges. For the Tiger Claw repo specifically, use the specialized `tiger-doc-keeper` instead (it knows that repo's SOTU/PROGRESS/CI guards).
---

# doc-keeper

The **universal** Document Keeper. It kills "doc drift" on whatever project you're
in: work lands (PRs merge, conventions get decided) but the canonical docs that
describe current state go stale, so they can't be trusted. This skill dispatches
the **`doc-keeper` subagent** to reconcile those docs to reality.

**Project-agnostic by design** — it does NOT assume a fixed doc set. It detects the
project (the git repo you're in) and **discovers that project's living docs**, then
reconciles only those. Works for a product repo, a library, a skills folder, a
script. For the **Tiger Claw** repo, use [`tiger-doc-keeper`](../tiger-doc-keeper/SKILL.md)
— the specialized sibling that knows Tiger's exact dashboard + doc-CI guards.

It is the complement to `context-keeper`:
- `context-keeper` writes the append-only session flight recorder (`.claude/sessions/`).
- `doc-keeper` reconciles the project's living/dashboard docs to current truth.

## When to use

- After a PR merges (the change landed — make the docs say so).
- When a decision or convention is locked (record it where that project records decisions).
- At **session close**, AFTER `context-keeper` writes its snapshot.
- On demand: "reconcile the docs", "the docs are stale", "update the README/CHANGELOG".

## How to run it

Dispatch the `doc-keeper` agent with the `Agent` tool. It's self-contained — it
discovers the project's docs and procedure itself. Give it the context it can't derive:

```
Agent(
  subagent_type: "doc-keeper",
  description: "Reconcile this project's living docs to reality",
  prompt: "Reconcile <project>'s living docs to current reality.
           - Project root: <path or 'the repo I'm in'>
           - What landed this session: <PRs merged, decisions locked>
           - Any doc you already know is stale: <name + what's wrong>
           Discover this project's living docs (README, CHANGELOG, status/handoff
           doc, ADRs, docs/, domain index, punch-lists), establish ground truth from
           git + merged PRs + any .claude/sessions snapshot, correct the drift with
           surgical edits, stage ONE docs PR on the repo's default branch
           (branch docs/reconcile-YYYY-MM-DD), do NOT merge, return the drift
           report + PR URL."
)
```

Run it in a worktree (`isolation: "worktree"`) if the working tree has in-progress
code changes you don't want disturbed.

## Hard rules (the agent enforces these; you enforce them too)

- **Docs only. Never code, schema, or secrets.** A doc fix that needs a code change → STOP and flag.
- **Never push to the default branch directly. One docs PR. Merge only on the user's explicit go.**
- **Evidence-grounded** — every doc update traces to a PR / commit / snapshot / the live code; unverifiable claims get flagged, not "fixed."
- **Discover, don't assume.** Reconcile the docs the project actually has; don't invent a dashboard it doesn't use.
- **Don't duplicate** context-keeper (sessions/) or auto-memory.
- Timeless-rules docs (`CLAUDE.md`, `AGENTS.md`, `README`-of-rules, `SACRED_WIRING.md`) are touched only on a real rule change, and only after explicit approval.

## After it returns

Relay the agent's drift report and the docs PR URL to the user. The PR is NOT merged —
surface it for their per-PR go. Put anything needing a human decision in front of them.
