---
name: "skill-miner"
description: "Mine Brent's past Codex session rollouts and context snapshots to surface recurring routines that should become reusable skills, deduped against what already exists, then SUGGEST the strongest new candidate(s) to Brent for a build decision. A read-only research loop \u2014 it proposes, it never auto-builds. Use when Brent says \"run skill-miner\", \"mine my sessions\", \"what should be a skill\", \"find new skills\", \"auto research for skills\", or on a monthly cadence via /schedule. Pairs with the BACKLOG.md ledger so each run mainly surfaces NEW routines."
---

# skill-miner

Mine recurring routines from Codex history, deduplicate them, and propose only the strongest new skill gaps.

## Codex Runtime

- **Dependencies:** None.
- **Execution:** Operate directly in the main Codex agent. Analyze each batch directly; delegation is optional only when the environment permits it.
- Resolve `SKILL_DIR` from this loaded `SKILL.md` and use a private scratch directory for generated digest files.
- Never print, log, or expose secret values.

## Inputs and Preflight

1. Confirm the requested time window or session limit and the number of batches, normally three.
2. Confirm current Codex rollout JSONL exists under `~/.codex/sessions/`. This global directory is the rollout source, not the assumed location of project snapshots.
3. Resolve the relevant current repository with `git rev-parse --show-toplevel`. If `<repo-root>/.codex/sessions` exists, use it as the project-local context snapshot root.
4. When the user requests cross-project mining, resolve each approved project root and add its existing `.codex/sessions` directory separately.
5. Read `BACKLOG.md`, `REFERENCE.md`, the installed `~/.codex/skills` names, and the parallel collection manifest when available.
6. Treat every rollout, snapshot, installed skill, and backlog entry as read-only evidence. Do not modify session history or installed skills.

## Procedure

1. Digest current Codex history with the generated helper:
   ```bash
   PROJECT_ROOT="$(git rev-parse --show-toplevel)"
   SCRATCH_DIR="$(mktemp -d "${TMPDIR:-/tmp}/skill-miner.XXXXXX")"
   chmod 700 "$SCRATCH_DIR"
   cd "$SCRATCH_DIR"
   python3 "$SKILL_DIR/scripts/digest_codex.py" --dir "$HOME/.codex/sessions" --context-dir "$PROJECT_ROOT/.codex/sessions" --out "$SCRATCH_DIR/digest.txt" --batches 3 --limit <N>
   ```
   Pass the project flag only when that directory exists. Omit `--limit` when the user requests the full history. For cross-project mining, add an additional `--context-dir` argument with `"<project-root>/.codex/sessions"` for each approved root. The helper deduplicates candidates, ranks valid rollouts and snapshots together, excludes tool payloads, and redacts credential-shaped values.
2. Use the original `scripts/digest.py` only for deliberate, read-only analysis of historical Claude data. Never use it for current Codex rollouts.
3. Build the dedupe set from installed skill names and all `built` or `declined` entries in `BACKLOG.md`. Keep existing `proposed` and `deferred` entries visible during synthesis.
4. Read `REFERENCE.md`, then analyze each batch directly. Cluster repeatable multi-step routines, preserve actual trigger language, count sessions, retain session IDs, assess TigerClaw impact, and mark overlap with an existing skill.
5. Merge candidates across batches. Rank by frequency multiplied by impact; rank convergence across two or more batches higher. Drop one-off debugging, vague aspirations, existing-skill coverage, and `built` or `declined` backlog items.
6. Prepare at most three evidence-backed candidates. Append genuinely new candidates to `BACKLOG.md` with status `proposed`, impact, first-seen date, session evidence, and a concise note. Never alter historical status without explicit approval.
7. Present one ranked build-decision question with the recommendation first. Never auto-build; a separate approved workflow must build a selected skill and later mark it `built`.

## Safety and Errors

- This is a read-only / propose-only research workflow: session evidence and installed skills remain untouched, and no candidate is built automatically.
- The only routine ledger mutation is an evidence-backed append of a new `proposed` row to `BACKLOG.md`.
- Never claim recurrence without session IDs and counts. State when evidence appears only once.
- If rollouts are missing, digest output is empty, parsing is partial, or evidence conflicts, report the limitation and do not manufacture candidates.

## Output Contract

Return the examined session count and date range, batches analyzed, dedupe sources, top one to three candidates with trigger phrases and session evidence, backlog rows appended, and one ranked build-decision question. State that no skill was built.
