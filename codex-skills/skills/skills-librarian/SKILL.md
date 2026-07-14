---
name: "skills-librarian"
description: "Maintain Brent's INSTALLED skill library \u2014 audit ~/.codex/skills for integrity (name\u2194folder mismatches, missing SKILL.md, stray files, dead symlinks), reconcile it against ~/Desktop/Truth/SKILLS-INDEX.md (what's new vs stale), and regenerate that index preserving his categories. Read-only audit by default; fixes are per-item approved; it QUARANTINES cruft to the dump, never deletes. The maintenance complement to skill-miner (miner finds new skills; librarian keeps the shelf clean). Use when Brent says \"skills librarian\", \"clean up my skills\", \"skills are a mess\", \"dedupe my skills\", \"update the skills index\", \"what skills do I have\", or after building/installing skills."
---

# skills-librarian

Audit the installed Codex skill shelf, reconcile its index and parallel manifest, and propose repairs before changing anything.

## Codex Runtime

- **Dependencies:** Python 3; local ~/.codex/skills root; local ~/.agents root; local ~/Desktop/Truth/SKILLS-INDEX.md; parallel codex-skills manifest repository
- `Python 3`
- `local ~/.codex/skills root`
- `local ~/.agents root`
- `local ~/Desktop/Truth/SKILLS-INDEX.md`
- `parallel codex-skills manifest repository`
- **Execution:** Operate directly in the main Codex agent.
- Resolve `SKILL_DIR` from this loaded `SKILL.md`; the audit script accepts only `SKILLS_DIR` and `SKILLS_INDEX`, while the backup script accepts `SKILLS_DIR` and `AGENTS_SRC`.
- Never print, log, or expose secret values.

## Inputs and Preflight

1. Confirm `python3` is available. Set `SHELF="$HOME/.codex/skills"`, `AGENTS="$HOME/.agents"`, and `INDEX="$HOME/Desktop/Truth/SKILLS-INDEX.md"`; identify the parallel repository containing `codex-skills/manifest.yaml`.
2. Confirm the shelf, agent root, curated index, parallel manifest, and copied scripts exist. If any mandatory dependency is unavailable, stop without changing either collection and report the missing command or path.
3. Record whether the shelf is Git-backed before proposing backup operations.
4. Treat audits, index comparisons, and manifest reads as read-only. Require per-item approval before every rename, metadata edit, quarantine move, index edit, or backup mutation.
5. Keep dump and archive directories separate from the live shelf. Do not classify intentional support directories as cruft merely because they lack `SKILL.md`.

## Procedure

1. Run the integrity audit with the script's exact environment input:
   ```bash
   SKILLS_DIR="$HOME/.codex/skills" python3 "$SKILL_DIR/scripts/audit.py"
   ```
2. Compare the live shelf with the curated index:
   ```bash
   SKILLS_DIR="$HOME/.codex/skills" SKILLS_INDEX="$INDEX" python3 "$SKILL_DIR/scripts/audit.py" diff-index
   ```
   Treat grouped-name parsing as approximate and verify every stale result against the actual index.
3. Read `codex-skills/manifest.yaml` from the parallel collection. Compare its output names with installed names, distinguish managed links from personal skills, and report manifest outputs that are missing, extra, or broken without changing either collection.
4. Present integrity issues, index drift, manifest drift, likely duplicates, and business-specific skills. Propose one repair per item and wait for per-item approval.
5. Apply only approved repairs. Resolve name/folder mismatches as directed. Move cruft to an approved quarantine directory; never delete it. Add intentional support directories to the audit ignore policy only when the index explicitly blesses them.
6. Regenerate inventory with:
   ```bash
   SKILLS_DIR="$HOME/.codex/skills" python3 "$SKILL_DIR/scripts/audit.py" inventory
   ```
   Preserve curated categories; update membership, one-line descriptions, audit date, and count without flattening the index.
7. Re-run integrity, diff-index, and manifest comparisons. Confirm zero unexplained integrity issues and reconcile live/index counts.
8. Propose backup separately. The source script can mutate a mirror even before PR creation, so run it only after approval. Pass only inputs it actually accepts:
   ```bash
   SKILLS_DIR="$HOME/.codex/skills" AGENTS_SRC="$HOME/.agents" "$SKILL_DIR/scripts/backup.sh"
   ```
   Use `--confirm` only after the user confirms the exact sync; open a branch and PR, never push the default branch or merge without separate per-PR approval.

## Safety and Errors

- Read-only until approved. Never rename, edit, move, install, unlink, or back up an item without its approval.
- Quarantine, never delete. A suspected duplicate remains live until the user approves its move.
- Do not expose credentials from Git remotes, configs, diffs, or environment variables.
- Stop when the audit fails unexpectedly, a link target is ambiguous, the index and manifest conflict, the secret scan fails, or the backup branch is not based on a clean default branch.

## Output Contract

Return before/after counts, integrity issues, index NEW/STALE results with approximation caveats, parallel-manifest drift, each proposed and approved action, quarantine destinations, verification results, and any backup PR URL. State which actions remain unapproved and confirm that nothing was deleted.
