---
name: "claude-memory-index"
description: "Use when the user wants to index a repository into claude-memory, start using claude-memory on a new project, or re-index after significant history. Examples: \"index the lokumcu repo\", \"set up claude memory for this project\", \"re-index everything\""
---

# Index a Repository with claude-memory

## When to Use

- Starting claude-memory on a new repository for the first time
- After a major history rewrite or large batch of commits
- User explicitly asks to (re-)index a project
- Setting up claude-memory for a team member's repo

## Workflow

```
1. Confirm the repo path with the user (default: current directory)
2. Run a dry-run first to show what will be indexed
3. Ask if the user wants to limit commit count (useful for very large repos)
4. Run the real index
5. Show the summary and confirm the post-commit hook is installed
6. Run claude-memory install to register the MCP server
```

## Checklist

```
- [ ] Confirmed repo path
- [ ] Ran dry-run to preview commit count and filter results
- [ ] Agreed on --limit if repo has >1000 commits
- [ ] Completed indexing with 0 errors
- [ ] post-commit hook is installed and executable
- [ ] MCP server registered in ~/.codex/config.toml
- [ ] Reminded user to restart the active Codex session
```

## Commands

### Dry run (preview what will be indexed)
```bash
source .venv/bin/activate
python scripts/claude_memory_indexer.py \
  --repo-path /path/to/repo \
  --user-id my-repo-name \
  --dry-run
```

### Full index
```bash
python scripts/claude_memory_indexer.py \
  --repo-path /path/to/repo \
  --user-id my-repo-name
# Add --limit 500 for large repos (indexes 500 newest commits)
```

### Install claude-memory MCP integration
```bash
claude-memory install \
  --repo-path /path/to/repo \
  --user-id my-repo-name
```

### Install post-commit hook (auto-updates on every commit)
```bash
cp .git/hooks/post-commit /path/to/repo/.git/hooks/post-commit
chmod +x /path/to/repo/.git/hooks/post-commit
```

### Or with pip-installed CLI
```bash
cd /path/to/repo
claude-memory index --repo-path . --user-id my-repo-name
claude-memory install --repo-path . --user-id my-repo-name
```

## Expected Output

```
Repo   : lokumcu (/Users/.../lokumcu)
User ID: lokumcu
Chroma : 0 commits already indexed
Walking history (branch=HEAD, limit=all) …
Found 42 commits to evaluate
Stored  [d0eebd0d] feat(dealers): add IBAN/bank_name fields...  (fix)
Stored  [f875d899] fix(payments): allow payment_failed → preparing...  (fix)
...
Done. {'total_evaluated': 42, 'stored': 39, 'skipped_irrelevant': 3, 'errors': 0}
```

## Notes

- **Skipped irrelevant**: Commits with no signal keywords (e.g. "k", "wip", "merge") are skipped by design. This keeps the index signal-rich.
- **Deduplication**: Safe to run multiple times — ChromaDB deduplicates by commit hash.
- **Large repos**: For repos with >10k commits, use `--limit 1000` to index the most recent 1000. You can always re-run with a higher limit later.
- **user-id**: Use a distinct ID per repo (e.g. `lokumcu`, `myapp`) so multiple repos can coexist in the same index.

## Codex Runtime

Keep `claude-memory` as the external product name. Use its actual MCP tools when available; otherwise preflight and use the `claude-memory` CLI.

Never expose or print secret, credential, or token values.

Mandatory dependencies:
- `claude-memory CLI or MCP`
- `Git repository`

Preflight each dependency using MCP/app capability discovery, CLI availability/version checks, read-only filesystem or Git checks for repositories, and provider auth-status commands without printing secrets, credentials, or tokens.
If any mandatory dependency is unavailable, stop and report a concise blocked state naming the missing dependency and the next action needed.
