---
name: context-keeper
description: Write the append-only per-session flight recorder to the CURRENT project's .claude/sessions/ — a dated, numbered snapshot of what THIS session decided, discovered, shipped, verified (vs not), and the next step. Project-agnostic — works for any project; defaults to the current git repo root (override with CONTEXT_KEEPER_DIR). Records the session (the raw record); a separate docs-reconcile step then updates the project's living docs. Use at session close before reconciling docs, or when Brent says "context keeper", "save the session", "write the flight recorder", "snapshot this session", "record the session". Append-only — one new file per session, never edits prior snapshots, never overclaims.
---

# context-keeper

Writes the **session flight recorder**: one append-only file per working session at
`<project-root>/.claude/sessions/YYYY-MM-DD_session-NNN.md` — where `<project-root>` is
the current git repo (or `CONTEXT_KEEPER_DIR` if set). It captures what happened so the
next session resumes with full context and nothing rots. Works for ANY project, not just one.

It is the **complement to the docs-reconcile step**:
- **context-keeper** (this) — writes the immutable session snapshot (`.claude/sessions/`).
- **the project's living-docs reconcile** — brings the project's "dashboard"/status docs
  (whatever it has: README, CHANGELOG, status/handoff doc, ADRs, a domain index, punch-lists)
  back to current truth. On TigerClaw that's the `doc-keeper` agent; on another project it's
  reconciling those docs directly. context-keeper does NOT do this — it's the raw record only.

At session close the order is: **context-keeper → docs reconcile** (and `closing-ritual`
wraps both). Don't duplicate the docs step or auto-memory here.

## Workflow

1. **Scaffold the next file** (don't guess the number):
   `bash scripts/new-session.sh "<one-to-three-line arc of the session>"`
   It computes the next session number from disk (handles gaps), stamps today's date,
   and writes a skeleton. It refuses to overwrite. (`--number` / `--path` are read-only.)
2. **Fill it from THIS session's real history** — sections already in the skeleton:
   - **Decisions** — what was decided AND what was *ruled out* (keep ruled-out; it stops re-litigation).
   - **Discoveries** — ground truth learned that wasn't obvious before.
   - **Shipped / changed** — PR numbers, merge SHAs, deploys, with **UTC timestamps** and live proof where it applies (a health check, a passing run, observed output).
   - **Verified vs unverified** — what was proven live and *how*; and what is claimed but NOT exercised. **Name the gap; never paper over it.**
   - **Open threads / next step** — the single most concrete next action.
3. **Ground every claim.** Same bar as `ship-it`: never write "shipped" / "proven" without the evidence. If it's unverified, label it unverified. Honesty over tidiness.
4. **Append-only.** One new file; never edit a prior snapshot. Corrections go in the new session's Discoveries.

## Boundaries

- Writes ONLY to `.claude/sessions/`. Does not touch dashboard docs (doc-keeper's job),
  timeless-rules docs (AGENTS.md/CLAUDE.md/SACRED_WIRING.md), or code.
- Config: `CONTEXT_KEEPER_DIR` overrides the sessions directory (default = the current
  git repo root's `.claude/sessions`, else `$PWD/.claude/sessions`).

## Quick start

```bash
bash scripts/new-session.sh --number      # what the next session number will be (read-only)
bash scripts/new-session.sh "SWOT → shipped #1221 WhatsApp two-way → verified live"
# then open the CREATED file and fill the five sections from real history
```
