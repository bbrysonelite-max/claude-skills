---
name: "skills-librarian"
description: "Maintain Brent's INSTALLED skill library \u2014 audit ~/.codex/skills for integrity (name\u2194folder mismatches, missing SKILL.md, stray files, dead symlinks, inactive-profile leaks), reconcile it against the Git-backed codex-skills/SKILLS-INDEX.md (what's new vs stale), and regenerate that index preserving his categories. Read-only audit by default; fixes are per-item approved; it QUARANTINES cruft to the dump, never deletes. The maintenance complement to skill-miner (miner finds new skills; librarian keeps the shelf clean). Use when Brent says \"skills librarian\", \"clean up my skills\", \"skills are a mess\", \"dedupe my skills\", \"update the skills index\", \"what skills do I have\", or after building/installing skills."
---

# skills-librarian

Audit the installed Codex skill shelf, reconcile its index and parallel manifest, and propose repairs before changing anything.

## Codex Runtime

- **Dependencies:** Python 3; local ~/.codex/skills root; local ~/.agents root; Git-backed codex-skills/SKILLS-INDEX.md; codex-skills active profile; parallel codex-skills manifest repository
- `Python 3`
- `local ~/.codex/skills root`
- `local ~/.agents root`
- `Git-backed codex-skills/SKILLS-INDEX.md`
- `codex-skills active profile`
- `parallel codex-skills manifest repository`
- **Execution:** Operate directly in the main Codex agent.
- Resolve `SKILL_DIR` from this loaded `SKILL.md`. Set `CODEX_SKILLS_REPO` to the Git worktree containing `codex-skills/manifest.yaml`; the audit script also accepts `SKILLS_DIR` and `SKILLS_INDEX`, while the backup script requires `CODEX_SKILLS_REPO`, `SKILLS_DIR`, and one explicit reviewed `--path` per repository-relative file.
- Never print, log, or expose secret values.

## Inputs and Preflight

1. Confirm `python3` is available. Set `SHELF="$HOME/.codex/skills"`, `AGENTS="$HOME/.agents"`, and `CODEX_SKILLS_REPO` to the parallel repository containing `codex-skills/manifest.yaml`. Set `INDEX="$CODEX_SKILLS_REPO/codex-skills/SKILLS-INDEX.md"` and `PROFILE="$CODEX_SKILLS_REPO/codex-skills/active-profile.json"`.
2. Confirm the shelf, agent root, curated index, active profile, parallel manifest, and copied scripts exist. If any mandatory dependency is unavailable, stop without changing either collection and report the missing command or path.
3. Confirm `CODEX_SKILLS_REPO` is Git-backed and has an `origin/main` tracking reference. The helper audits the installed shelf but fetches and compares this generated-shelf repository. A repository behind `origin/main` is stale and fails audit/diff-index; a fetch failure still runs the cached comparison. Missing or unusable cached refs are unverified and return nonzero. Ahead is informational. Use `SKILLS_NO_FETCH=1` only when deliberately offline: cached comparison still runs, but upstream freshness is unverified without a successful fetch.
4. Treat audits, index comparisons, and manifest reads as read-only. Require per-item approval before every rename, metadata edit, quarantine move, index edit, or backup mutation.
5. Keep dump and archive directories separate from the live shelf. Do not classify intentional support directories as cruft merely because they lack `SKILL.md`.

## Procedure

1. Run the integrity audit with the script's exact environment input:
   ```bash
   SKILLS_DIR="$HOME/.codex/skills" CODEX_SKILLS_REPO="$CODEX_SKILLS_REPO" python3 "$SKILL_DIR/scripts/audit.py"
   ```
2. Compare the live shelf with the curated index:
   ```bash
   SKILLS_DIR="$HOME/.codex/skills" SKILLS_INDEX="$INDEX" CODEX_SKILLS_REPO="$CODEX_SKILLS_REPO" python3 "$SKILL_DIR/scripts/audit.py" diff-index
   ```
   Treat grouped-name parsing as approximate and verify every stale result against the actual index. Never continue an index comparison when the generated shelf is stale against `origin/main`.
3. Read `codex-skills/manifest.yaml` and `codex-skills/active-profile.json` from the parallel collection. Compare active manifest outputs (all outputs minus the profile's inactive names) with installed names. Distinguish managed links, intentionally inactive skills, and personal skills; report active outputs that are missing, extra, or broken without changing either collection.
4. Present integrity issues, index drift, manifest drift, likely duplicates, and business-specific skills. Propose one repair per item and wait for per-item approval.
5. Apply only approved repairs. Resolve name/folder mismatches as directed. Move cruft to an approved quarantine directory; never delete it. Add intentional support directories to the audit ignore policy only when the index explicitly blesses them. Sync the generated collection through `python3 "$CODEX_SKILLS_REPO/codex-skills/scripts/sync_active.py"` so inactive skills cannot leak back into discovery.
6. Regenerate inventory with:
   ```bash
   SKILLS_DIR="$HOME/.codex/skills" CODEX_SKILLS_REPO="$CODEX_SKILLS_REPO" python3 "$SKILL_DIR/scripts/audit.py" inventory
   ```
   Preserve curated categories; update membership, one-line descriptions, audit date, and count without flattening the index.
7. Re-run integrity, diff-index, and manifest comparisons. Confirm zero unexplained integrity issues and reconcile live/index counts.
8. Propose the exact backup file allowlist separately. Run a path-limited dry-run only after approval:
   ```bash
   SKILLS_DIR="$HOME/.codex/skills" CODEX_SKILLS_REPO="$CODEX_SKILLS_REPO" "$SKILL_DIR/scripts/backup.sh" --path "<reviewed-repo-relative-file>"
   ```
   Repeat `--path "<reviewed-repo-relative-file>"` for every exact file and inspect the complete reported patch. The helper must preserve unrelated working-tree changes and the protected `.agents-backup` provenance tree. Use `--confirm` only after the user confirms that exact allowlist; open a branch and PR, never push the default branch or merge without separate per-PR approval.

## Safety and Errors

- Read-only until approved. Never rename, edit, move, install, unlink, or back up an item without its approval.
- Quarantine, never delete. A suspected duplicate remains live until the user approves its move.
- Do not expose credentials from Git remotes, configs, diffs, or environment variables.
- Never mirror `~/.agents` into `.agents-backup`, run an unbounded `git add -A`, or stage a file outside the approved allowlist.
- Stop when the audit fails unexpectedly, mirror freshness is unverified, a link target is ambiguous, the index and manifest conflict, the secret scan fails, or the backup branch is not based on a clean default branch.

## Output Contract

Return before/after active counts, inactive-profile membership, integrity issues, index NEW/STALE results with approximation caveats, parallel-manifest drift, each proposed and approved action, quarantine destinations, verification results, and any backup PR URL. State which actions remain unapproved and confirm that nothing was deleted.
