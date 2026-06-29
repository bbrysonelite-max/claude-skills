---
name: closing-ritual
description: "Run the end-of-session closing ritual on ANY project so a working session ends clean and verified — all work merged, tests green, the project's living docs matching the code (zero drift), durable state saved to memory, git clean, and a short handoff. Project-agnostic: it locates whatever project you worked in and gathers ITS docs (you don't remember anything between sessions — collect the real artifacts). Use when the user says 'close out', 'closing ritual', 'wrap up', 'wind down', 'end of session', 'let's call it', or is otherwise ending a session."
---

# Closing Ritual

Leave the work **clean, verified, and handed off** — so the next session (you or
anyone) resumes in one step and nothing rots between now and then.

**This is universal.** It is NOT tied to any one project. "Use the closing skill" runs
the same on a product repo, a skills folder, a one-off script — because the first move is
always: figure out *which* project this was and gather *its* documents. You don't carry
memory between sessions; the close re-grounds on the real artifacts every time.

Run these in order. **Verify each with a command — never claim done from memory.**
If a step can't be satisfied, name the gap explicitly; do not paper over it.

## The checklist

Create a TodoWrite item per step and work them top to bottom.

1. **Locate the project & gather its docs.** Establish what you were working in this
   session: the git repo root (`git rev-parse --show-toplevel` from where the work
   happened), or the working dir if it's not a repo. Then **collect that project's
   living documents** — whatever it actually has: `README`, `CHANGELOG`, `docs/`, a
   status/handoff doc (e.g. `SOTU`/`NEXT_SESSION`/`PROGRESS`/`TO-DO`), ADRs, a domain
   index (e.g. `SKILLS-INDEX.md` for the skills folder), punch-lists. Don't assume a
   doc set — discover it. State the project and the docs you found; this is the ground
   truth the rest of the close reconciles against.
2. **Merge & branch check.** For every PR opened this session (in *this* repo), confirm
   state is `MERGED` (`gh pr view <n> --json state`). Delete merged feature branches.
   List any still-open PRs and say whose call the merge is. No orphan branches.
3. **Tests green.** Detect and run *this project's* test suite (e.g. `npm test`, `pytest`,
   `make test`, a `scripts/` check). Report the **real** pass count from the output, not a
   remembered number. If the project has no suite, say so plainly and run whatever
   verification does exist (scripts, linters, a manual exercise). If anything fails, stop
   and surface it.
4. **Session snapshot — `context-keeper`.** BEFORE reconciling docs, write the append-only
   flight recorder for THIS project: invoke **`context-keeper`** (it defaults to the
   current repo's `.claude/sessions/`; it scaffolds the next-numbered file — fill its five
   sections from this session's real history). The raw record runs first.
5. **Docs zero-drift.** Reconcile the project's living docs (gathered in step 1) to what
   the code/state actually is now. Spot-check the claims that changed this session, or
   spawn a verifier agent for a true zero-drift check; fix any drift. Use the
   project-agnostic **`doc-keeper`** skill (it discovers and reconciles whatever docs
   the project has); for the **Tiger Claw** repo use the specialized **`tiger-doc-keeper`**
   (it knows that repo's SOTU/PROGRESS set + doc-CI guards). Leave evergreen process
   docs (CLAUDE.md / AGENTS.md / GROUND_TRUTH-style) alone.
6. **Memory.** Write the session's durable facts to memory: what shipped, key decisions
   and *why*, any new working rule. Convert relative dates to absolute. Add/refresh the
   one-line pointers in `MEMORY.md`. Don't save what the repo/git already records.
7. **Git clean.** End on the project's default branch, pulled up to date, no uncommitted
   changes. Confirm with `git status --short --branch`. (For a skills/library change,
   "clean" means backed up too — see its own backup flow, never a direct push to main.)
8. **Handoff.** Write a short **Resume here**: where things stand + the single concrete
   next step. Put it in the project's memory or a NEXT/handoff doc so it's found first.
9. **Report.** Give the operator one scannable close: the project, what shipped, the
   verified test count, doc/memory/git state, open PRs (and whose call), and the next
   step. State "done" only for what a command proved. Name any unverified gap plainly.

## Honesty bar

This ritual exists to prevent silent rot and false confidence. A green claim without
command output is not done. If you didn't verify it, say so. If a step doesn't apply to
this project (no PRs, no test suite, no dashboard docs), mark it `N/A` with the reason —
don't fabricate an artifact to satisfy the step.

## Scope

A wrap-up, not new work. Don't start features here. If the close reveals a real problem
(failing test, drift, un-merged work), surface it and let the operator decide — fixing it
may be its own task, not part of the close.
