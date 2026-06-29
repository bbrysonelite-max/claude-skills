---
name: vault-hygiene
description: "Use when performing daily vault maintenance, when indexes may be stale, when files are misplaced or missing frontmatter, when STATUS.md or memory files have drifted from reality, or when invoked by the daily scheduled trigger. Also use after any bulk ingestion or file reorganization."
meta: "Brent Bryson Personal Daily Checks"
---

# Vault Hygiene

Daily audit and repair of the Obsidian vault at `~/Desktop/vault-personal/`. Keeps indexes accurate, frontmatter valid, context files current, and agent memory honest.

**Canonical rules:** `SPEC.md` > `CLAUDE.md` > everything else. Read both before starting.

## When to Run

- Daily scheduled trigger fires
- User says `/vault-hygiene` or asks to "clean up the vault"
- After any bulk ingestion (Wispr, OpenAI, Claude Code, NotebookLM, Manus)
- After any file reorganization or migration
- When you suspect indexes or STATUS.md are stale

## Audit Procedure

Run these phases in order. Each phase produces a findings list. At the end, fix what can be fixed automatically and report the rest.

### Phase 1: Index Audit

For every folder that should have an `index.md` (per SPEC.md vault structure):

1. **Glob** the folder for all files
2. **Read** the `index.md`
3. Compare: flag files on disk not in the index, entries in the index not on disk, wrong file counts
4. **Fix:** Rewrite stale indexes to match reality. Preserve the folder description paragraph. Update file count and linked file list.

Folders to check:
- `01_Active_Projects/` and each subfolder
- `02_The_Library/` and `Book_1/`, `Book_2/`, `Book_3/`
- `03_The_Stream/` and each subfolder (`Wispr_Flow/`, `NotebookLM/`, `OpenAI/`, `Claude_Code/`, `Manus/`)
- `04_The_Synthesizer/` and `Atomic_Notes/`, `Maps_of_Content/`
- `05_System_and_Templates/` and `Templates/`, `Scripts/`

### Phase 2: Frontmatter Validation

Scan all `.md` files (excluding `index.md`, `CLAUDE.md`, `SPEC.md`, `STATUS.md`, `README.md`, `DECISIONS.md`, `Dashboard.md`).

Required fields: `title`, `source`, `type`, `date`, `tags`

Validate:
- `source` is one of: `wispr_flow`, `notebooklm`, `openai`, `claude_code`, `manus`, `book`, `synthesis`
- `type` is one of: `voice_transcript`, `infographic`, `ai_conversation`, `coding_session`, `task_output`, `book_chapter`, `atomic_note`, `moc`, `project`
- `date` is valid `YYYY-MM-DD`
- Type-specific extra fields are present (see SPEC.md Rule 2)

**Fix:** Add missing fields where the correct value can be inferred from file path or content. Flag ambiguous cases for user review.

### Phase 3: Orphan Detection

Find files that exist in the vault but are not referenced in ANY `index.md`:
1. Collect all files from disk under the five top-level folders
2. Collect all file references from all `index.md` files
3. Diff — orphans are files on disk with no index entry

For each orphan, determine correct location by examining content and frontmatter:
- Has `type: project` or lives under `01_Active_Projects/` path → belongs in `01_Active_Projects/`
- Has `source: book` or `type: book_chapter` → belongs in `02_The_Library/`
- Has source matching a stream type → belongs in `03_The_Stream/{source}/`
- Has `type: atomic_note` or `type: moc` → belongs in `04_The_Synthesizer/`

**Fix:** Move misplaced files, update their index. Flag files where destination is ambiguous.

### Phase 4: STATUS.md Refresh

Read current `STATUS.md`. Then gather ground truth:

1. Count files in each folder
2. Check which ingestion scripts exist and which stream folders have content
3. Check `04_The_Synthesizer/` for atomic notes and MOCs
4. Check `05_System_and_Templates/Templates/` for template files

Rewrite STATUS.md sections:
- **Done:** Only list items that are actually done (files exist, indexes accurate)
- **In progress:** Items partially complete
- **Not started:** Items with no files or empty folders
- **Known issues:** Carry forward unresolved issues, add new ones found in this audit
- **Update the "Last updated" date** to today

### Phase 5: Memory Staleness Audit

Read all files in `~/.claude/projects/-Users-brentbryson-Desktop-vault-personal/memory/`.

For each memory file:
1. Check if claims about files, paths, or state still match reality
2. Check if the memory's `description` still accurately summarizes the content
3. Flag memories older than 30 days for review

**Fix:** Update memories where the correct current state is clear. Delete memories that are completely obsolete. Flag ambiguous cases.

Update `MEMORY.md` index if any memory files were added, updated, or removed.

### Phase 6: Context Drift Detection

Check for contradictions between:
- `SPEC.md` vs `CLAUDE.md` (SPEC wins — update CLAUDE.md if they disagree)
- `STATUS.md` vs actual vault state (actual state wins — update STATUS.md)
- `MEMORY.md` entries vs memory file contents (fix index to match files)
- `Dashboard.md` vs actual vault structure (update Dashboard)

### Phase 7: Git Status Report

1. `git status` — report uncommitted changes
2. `git log origin/main..HEAD` — report unpushed commits
3. Flag any untracked files that should probably be committed or gitignored

Do NOT commit or push. Report findings and let the user decide.

## Output Format

After all phases, produce a summary:

```
## Vault Hygiene Report — YYYY-MM-DD

### Fixed
- [list of automatic fixes applied]

### Needs Attention
- [list of issues requiring user decision]

### Stats
- Total files: N
- Indexes audited: N (N fixed)
- Frontmatter issues: N (N auto-fixed, N need review)
- Orphans found: N (N routed, N ambiguous)
- Stale memories: N (N updated, N flagged)
- Git: N uncommitted changes, N unpushed commits
```

## Rules

- Never fabricate frontmatter values you can't infer. Flag and skip.
- Never delete content files. Only move, fix metadata, or flag.
- Never commit or push without explicit user approval.
- Follow the Eight Rules from SPEC.md at all times.
- If SPEC.md and CLAUDE.md disagree, update CLAUDE.md to match SPEC.md.
