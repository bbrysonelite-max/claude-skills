---
name: "doc-keeper"
description: "The project-agnostic Document Keeper. Use on ANY project when its living/dashboard docs have drifted from reality \u2014 after a PR merges, when a decision/convention is locked, at session close (after context-keeper), or when the user says \"reconcile the docs\" / \"update the docs\" / \"the docs are stale\". Runs the doc-keeper workflow directly; it DISCOVERS whatever living docs the project actually has (README, CHANGELOG, status/handoff docs, ADRs, docs/, a domain index, punch-lists) and reconciles them to current truth via ONE docs PR on the repo's default branch. Docs only \u2014 never code; never merges. For the Tiger Claw repo specifically, use the specialized `tiger-doc-keeper` instead (it knows that repo's SOTU/PROGRESS/CI guards)."
---

# doc-keeper

Reconcile the living documentation a project actually maintains. Use `tiger-doc-keeper` instead for `tiger-claw-v4-core`.

## Codex Runtime

- **Dependencies:** target Git repository; repository documentation checks
- `target Git repository`
- `repository documentation checks`
- **Execution:** Operate directly in the main Codex agent. Delegation is optional only when the environment permits it; direct execution remains complete.
- The direct main-agent workflow remains valid without delegation.
- Use repository-native Git, review, and documentation tooling.
- Never print, log, or expose secret values.

## Inputs and Preflight

1. Collect the project root, merged PRs or commits, locked decisions, known stale docs, and the latest `.codex/sessions/` snapshot when relevant.
2. Confirm the target is a Git repository and detect its actual default branch.
3. If the repository is Tiger Claw, stop and switch to `tiger-doc-keeper`.
4. Inspect repository instructions and documentation checks before editing.
5. Isolate from in-progress work when needed, fetch the remote, and branch `docs/reconcile-YYYY-MM-DD` from the remote default branch. Never work directly on the default branch.

## Procedure

1. Discover the living docs instead of assuming a fixed dashboard: README, CHANGELOG, status or handoff docs, ADRs, `docs/`, domain indexes, and punch lists.
2. Establish ground truth from the default-branch log, identified merge commits, PR metadata, the current code, and relevant session snapshots.
3. Build a drift list. For each claim, record its supporting commit, PR, code location, or snapshot; label unverifiable claims rather than repairing them by guesswork.
4. Correct only drifted documentation lines and follow each document's existing conventions. Preserve the distinction between live, planned, gated, and scaffolded work.
5. Touch timeless-rule docs only for a real rule change and only after explicit user approval.
6. Run every repository documentation check and inspect the working-tree diff. Build an explicit list containing only reviewed documentation paths.
7. Stage only that allowlist:
   ```bash
   git add -- <reviewed-doc-paths>
   ```
   Never stage code or unreviewed files.
8. Run `git diff --cached --name-only` and require the complete cached path list to equal the reviewed documentation allowlist. Inspect the entire cached patch with `git diff --cached`, then secret-scan that exact complete cached diff. Abort on credential-shaped content and report locations without values.
9. Commit with `git commit`, push only the topic branch, and open one PR against the default branch. Do not merge.

## Safety and Errors

- Docs only. Never edit code, schema, migrations, configuration, or secrets.
- Never push to the default branch and do not merge the PR.
- Do not invent a dashboard, duplicate context snapshots, or rewrite documents wholesale.
- If evidence conflicts, a code change is required, checks fail, or credentials appear, stop and flag the condition.

## Output Contract

Return a short drift report naming each stale doc, the surgical correction and evidence, checks run with results, the docs PR URL, all unverifiable claims, and every user decision still required. State explicitly that the PR is not merged.
