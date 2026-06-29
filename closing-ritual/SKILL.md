---
name: closing-ritual
description: "Run the end-of-session closing ritual so a working session ends clean and verified — all work merged, tests green, living docs matching the code (zero drift), durable state saved to memory, git clean, and a short handoff. Use when the user says 'close out', 'closing ritual', 'wrap up', 'wind down', 'end of session', 'let's call it', or is otherwise ending a session."
---

# Closing Ritual

Leave the work **clean, verified, and handed off** — so the next session (you or
anyone) resumes in one step and nothing rots between now and then.

Run these in order. **Verify each with a command — never claim done from memory.**
If a step can't be satisfied, name the gap explicitly; do not paper over it.

## The checklist

Create a TodoWrite item per step and work them top to bottom.

1. **Merge & branch check.** For every PR opened this session, confirm state is
   `MERGED` (`gh pr view <n> --json state`). Delete merged feature branches.
   List any still-open PRs and say whose call the merge is. No orphan branches.
2. **Tests green.** Run the full suite and report the **real** pass count from the
   output (not a remembered number). If anything fails, stop and surface it.
3. **Session snapshot — `context-keeper`.** BEFORE reconciling any docs, write the
   append-only session flight recorder: invoke the **`context-keeper`** skill
   (`new-session.sh` scaffolds the next-numbered file; fill its five sections from
   this session's real history). This is the raw record and must run first.
4. **Docs zero-drift — `doc-keeper`.** The living dashboard docs (SOTU, NEXT_SESSION,
   PROGRESS, TO-DO, ADRs, the relevant skill) must match what the code does now.
   Invoke the **`doc-keeper`** skill to reconcile them via one docs PR; spot-check the
   claims that changed this session, or spawn a verifier agent for a true zero-drift
   check. Fix any drift. Leave evergreen process docs (GROUND_TRUTH-style) alone.
5. **Memory.** Write the session's durable facts to memory: what shipped, key
   decisions and *why*, and any new working rule. Convert relative dates to
   absolute. Add/refresh the one-line pointers in `MEMORY.md`. Don't save what
   the repo/git already records.
6. **Git clean.** End on the default branch, pulled up to date, with no
   uncommitted changes. Confirm with `git status --short --branch`.
7. **Handoff.** Write a short **Resume here**: where things stand + the single
   concrete next step. Put it in the project memory or a NEXT/handoff doc so it's
   found first next time.
8. **Report.** Give the operator one scannable close: what shipped, the verified
   test count, doc/memory/git state, open PRs (and whose call), and the next step.
   State "done" only for what a command proved. Name any unverified gap plainly.

## Honesty bar

This ritual exists to prevent silent rot and false confidence. A green claim
without command output is not done. If you didn't verify it, say so.

## Scope

A wrap-up, not new work. Don't start features here. If the close reveals a real
problem (failing test, drift, un-merged work), surface it and let the operator
decide — fixing it may be its own task, not part of the close.
