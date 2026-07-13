---
name: "tiger-doc-keeper"
description: "The TIGER CLAW Document Keeper. Use when the Tiger Claw repo's living docs have drifted from reality — after a PR merges, when a decision/convention is locked, at session close, or when Brent asks to \"reconcile the Tiger docs\" / \"update the Tiger docs\". Runs the tiger-doc-keeper workflow directly to sync SOTU/NEXT_SESSION/PROGRESS/TO-DO/VERIFIED/ADRs/queues/Desktop punch-lists to current truth via ONE docs PR, respecting the repo's doc-CI guards. Docs only — never code. For ANY OTHER project, use the agnostic `doc-keeper` instead."
---

# tiger-doc-keeper

Reconcile the Tiger Claw living dashboard to current `origin/main` truth. Use `doc-keeper` for every other repository.

## Codex Runtime

- **Dependencies:** tiger-claw-v4-core repository; repository documentation checks
- `tiger-claw-v4-core repository`
- `repository documentation checks`
- **Execution:** Operate directly in the main Codex agent. Delegation is optional only when the environment permits it; direct execution remains complete.
- The direct main-agent workflow remains valid without delegation.
- Use repository-native Git, GitHub, and doc-check commands.
- Never print, log, or expose secret values.

## Inputs and Preflight

1. Require the `tiger-claw-v4-core` repository, merged PRs or decisions from this session, any named Desktop punch list, and known stale docs.
2. Read repository instructions and `SACRED_WIRING.md`; confirm the documented doc-check command.
3. Fetch `origin`, isolate from concurrent work, and create `docs/reconcile-YYYY-MM-DD` from `origin/main`. The default branch is `main`; never edit or push it directly.
4. Read the latest relevant `.codex/sessions/` snapshot as evidence, never as a substitute for merged state.

## Procedure

1. Inspect the complete Tiger dashboard:
   - `BIG-PICTURE.md`, the mandatory and highest-stakes flyover.
   - `SOTU.md`, `NEXT_SESSION.md`, `PROGRESS.md`, `TO-DO.md`, and `VERIFIED.md`.
   - `ARCHITECTURAL_DECISIONS.md`, `REFACTOR_QUEUE.md`, and `SECURITY_HARDENING_QUEUE.md`.
   - Any active Desktop punch list the user names.
2. Establish ground truth from `git log origin/main`, merge commits, PR metadata, `git show`, and the live code. Confirm migration numbers, flags, constraints, channel policy, and scope limits directly.
3. Reconcile surgically by each doc's convention:
   - Append verified shipped evidence to `VERIFIED.md`, distinguishing DARK from live.
   - Add a numbered architectural decision only when a decision is locked.
   - Move SOTU and PROGRESS current-state references to the latest defensible `origin/main` state.
   - Put follow-ups in NEXT_SESSION or TO-DO and link tracking issues.
   - Reconcile BIG-PICTURE whenever a locked decision, thesis, channel policy, or canon-map path changes.
4. Enforce the exact Tiger doc-CI rules:
   - The SOTU top entry leads with a SHA that is an ancestor of, or equal to, `origin/main` HEAD.
   - The PROGRESS timestamp is newer than the newest `origin/main` commit.
   - The merged-PR guard must resolve every PR number near merged wording as an actually merged PR; keep issue numbers away from that wording.
   - The LINE/drift_guard must contain no newly forbidden phrase.
5. Run the repository's documented doc check and inspect the working-tree diff. Build an explicit list containing only reviewed Tiger documentation paths.
6. Stage only that allowlist:
   ```bash
   git add -- <reviewed-doc-paths>
   ```
   Never stage code or unreviewed files.
7. Run `git diff --cached --name-only` and require the complete cached path list to equal the reviewed Tiger documentation allowlist. Inspect the entire cached patch with `git diff --cached`, then secret-scan that exact complete cached diff. Abort on any hit and report locations without values.
8. Commit with `git commit`, push only the topic branch, then open one docs PR against `main`. Do not merge.

## Safety and Errors

- Docs only. Never edit code, schema, migrations, Stripe, webhooks, `ai.ts`, configuration, or sacred wiring.
- Timeless-rule docs require a real rule change and explicit user approval.
- Never overstate DARK, gated, scaffolded, Telegram-only, or otherwise limited behavior.
- If evidence is unverifiable, doc CI fails, or a code change is needed, stop and flag it.

## Output Contract

Return a drift report mapping each correction to a PR, commit, or inspected code fact; include all doc-CI results, the docs PR URL, unverifiable items, and decisions requiring Brent. State explicitly that the PR is not merged.
