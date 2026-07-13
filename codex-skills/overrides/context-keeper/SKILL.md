---
name: "context-keeper"
description: "Write the append-only per-session flight recorder to the CURRENT project's .codex/sessions/ — a dated, numbered snapshot of what THIS session decided, discovered, shipped, verified (vs not), and the next step. Project-agnostic — works for any project; defaults to the current git repo root (override with CONTEXT_KEEPER_DIR). Records the session (the raw record); a separate docs-reconcile step then updates the project's living docs. Use at session close before reconciling docs, or when Brent says \"context keeper\", \"save the session\", \"write the flight recorder\", \"snapshot this session\", \"record the session\". Append-only — one new file per session, never edits prior snapshots, never overclaims."
---

# context-keeper

Write one immutable snapshot for the current working session. Reconcile living docs later with `doc-keeper`, or with `tiger-doc-keeper` for Tiger Claw.

## Codex Runtime

- **Dependencies:** None.
- **Execution:** Operate directly in the main Codex agent.
- Resolve `SKILL_DIR` from the directory containing this loaded `SKILL.md`.
- Never print, log, or expose secret values.

## Inputs and Preflight

1. Resolve the target repository with `git rev-parse --show-toplevel`; use the current directory only when it is not a Git repository.
2. Set `SESSION_DIR` to an explicitly supplied `CONTEXT_KEEPER_DIR`, otherwise to `<repo-root>/.codex/sessions`.
3. Review this session's decisions, discoveries, diffs, commits, test output, deployments, and live checks. Treat unsupported claims as unverified.
4. Query the next path without writing:
   ```bash
   CONTEXT_KEEPER_DIR="$SESSION_DIR" bash "$SKILL_DIR/scripts/new-session.sh" --path
   ```
5. Stop if that path already exists. Never choose an older file to edit.

## Procedure

1. Summarize the session arc in one to three evidence-grounded lines.
2. Scaffold exactly one new snapshot, always passing the Codex target explicitly:
   ```bash
   CONTEXT_KEEPER_DIR="$SESSION_DIR" bash "$SKILL_DIR/scripts/new-session.sh" "<session arc>"
   ```
3. Open only the newly created file and complete its five sections:
   - Decisions, including ruled-out options.
   - Discoveries grounded in observed evidence.
   - Shipped or changed work with PRs, SHAs, UTC timestamps, and live proof where applicable.
   - Verified versus unverified claims, naming every verification gap.
   - Open threads and one concrete next step.
4. Re-read the new snapshot against the session evidence. Downgrade any unsupported statement to unverified.
5. Report the new path. Leave living-doc reconciliation to the appropriate sibling skill.

## Safety and Errors

- Write only beneath the selected `.codex/sessions/` directory.
- Append by creating one new file; never edit a prior snapshot. Put corrections in the new snapshot's Discoveries section.
- Do not change code, dashboard docs, timeless-rule docs, or memory files.
- If the scaffold script fails, the target exists, or evidence is incomplete, stop and report the exact condition without claiming a snapshot was completed.

## Output Contract

Return the created snapshot path, its session number, the evidence used for verified claims, every unverified gap, and the single next action. Do not claim completion unless the new file exists and prior snapshots remain untouched.
