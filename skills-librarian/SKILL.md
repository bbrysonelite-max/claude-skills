---
name: skills-librarian
description: Maintain Brent's INSTALLED skill library — audit ~/.claude/skills for integrity (name↔folder mismatches, missing SKILL.md, stray files, dead symlinks), reconcile it against ~/Desktop/Truth/SKILLS-INDEX.md (what's new vs stale), and regenerate that index preserving his categories. Read-only audit by default; fixes are per-item approved; it QUARANTINES cruft to the dump, never deletes. The maintenance complement to skill-miner (miner finds new skills; librarian keeps the shelf clean). Use when Brent says "skills librarian", "clean up my skills", "skills are a mess", "dedupe my skills", "update the skills index", "what skills do I have", or after building/installing skills.
---

# skills-librarian

Keeps the installed skill shelf clean and the index true. The **live** folder
`~/.claude/skills/` is the source of truth Claude Code loads from; the dump
(`~/Desktop/skills:dump`) and `~/Desktop/skills-archive-*` are NOT live — never confuse them.

## Workflow

1. **Audit integrity** (read-only):
   `python3 scripts/audit.py`
   Reports total count + every integrity issue: folders with no `SKILL.md` / no `name:`,
   `name:`↔folder mismatches, stray non-folder files in the root, and dead symlinks.
   Exits non-zero if any issue (so it doubles as a gate).
2. **Reconcile against the index** (read-only):
   `python3 scripts/audit.py diff-index`
   Lists skills that are live-but-missing from `SKILLS-INDEX.md` (NEW) and index entries
   with no live folder (STALE), plus both counts.
3. **Present findings to Brent** — the integrity issues, the new/stale diff, and any
   suspected duplicates or business-specific skills. Propose a fix per item. Do not act yet.
4. **Apply fixes — per-item approval only** (his standing rule; never bulk-delete):
   - **Mismatch** → rename the folder to match `name:` (or fix `name:`), his call which.
   - **Cruft / incomplete / duplicate** (e.g. a folder with no usable `SKILL.md`) →
     **move it to `~/Desktop/skills:dump/`** — quarantine, never `rm`. He decides keep vs toss.
   - **New skills** → add to the index. **Stale entries** → remove from the index.
5. **Regenerate the index** — use `python3 scripts/audit.py inventory` (sorted `name<TAB>desc`)
   as the source data. **Preserve Brent's curated category groupings** (Core business, etc.);
   only refresh the per-skill one-liners, the membership, and the header line
   (`Audited & verified: <DATE>. Count: <N>`). Don't flatten his structure.
6. **Verify** (ground-truth, don't claim): re-run `audit.py` → 0 integrity issues; confirm
   the index count equals the live folder count. Report the before/after.
7. **Back up the shelf to its GitHub mirror** — the librarian owns keeping the backup current,
   not Brent's memory. `scripts/backup.sh` (dry-run) then `scripts/backup.sh --confirm`:
   integrity-gates on audit → `git add -A` (symlinks + nested repos are `.gitignore`d, so this
   is safe) → **secret-scans the staged diff** (hard stop on any hit) → commits + pushes to
   `origin/main` → verifies `HEAD==origin/main`. Run it whenever skills change (new skill,
   edit, index regen). Already-in-sync → it no-ops. **Mirror repo:** `bbrysonelite-max/claude-skills`
   (private). This is the one place `main` is pushed directly — it's a backup mirror, not a
   PR/deploy repo; the only mutation (`--confirm`) is gated like ship-it's merge.

## Rules

- **Read-only until approved.** Audit and propose; never rename/move/delete a skill without Brent's OK for that item.
- **Quarantine, never delete.** Cruft goes to the dump; deletion is always Brent's call.
- **Live ≠ dump ≠ archive.** Only operate on `~/.claude/skills/`. Flag the others, don't edit them.
- **Intentional non-skill folders are not cruft.** Some folders have no `SKILL.md` on purpose (e.g. `heygen-skills` = a source bundle the HeyGen skills symlink into; the index says "don't delete"). These live in the script's `IGNORE` set — never flagged, never quarantined. Add to `IGNORE` (don't quarantine) when the index blesses a support folder.
- **`diff-index` is APPROXIMATE** — the index uses grouped shorthand (`**a / -b / -c**`); the script expands it best-effort. Confirm against the actual index before removing an entry.
- Config: `SKILLS_DIR` (default `~/.claude/skills`), `SKILLS_INDEX` (default `~/Desktop/Truth/SKILLS-INDEX.md`).

## Quick start

```bash
python3 scripts/audit.py            # integrity report (read-only)
python3 scripts/audit.py diff-index # new vs stale vs the index
scripts/backup.sh                   # dry-run: gate + secret-scan + show what would sync
scripts/backup.sh --confirm         # commit + push the shelf to its private GitHub mirror
```
