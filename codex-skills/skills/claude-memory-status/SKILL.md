---
name: "claude-memory-status"
description: "Use when the user wants to check what is indexed, how many commits are in memory, or whether claude-memory is set up correctly. Examples: \"is claude memory set up?\", \"how many commits are indexed?\", \"check claude memory status\""
---

# Check claude-memory Status

## When to Use

- User asks if claude-memory is configured
- Before using search tools to confirm the index has data
- Troubleshooting empty search results
- After indexing to confirm it completed correctly

## Workflow

```
1. Run status command to check ChromaDB commit count
2. Check read-only whether the MCP server is configured in ~/.codex/config.toml
3. Check if post-commit hook is installed in the repo
4. Report findings and any gaps
```

## Checklist

```
- [ ] ChromaDB has > 0 commits indexed
- [ ] claude-memory MCP server is present in `~/.codex/config.toml`
- [ ] post-commit hook is installed and executable
- [ ] user-id matches between index and MCP server config
```

## Commands

### Check index size
```bash
source .venv/bin/activate
claude-memory status --repo-path /path/to/repo
```
Or via Python:
```python
from claude_memory import ChromaCommitIndex
c = ChromaCommitIndex()
print(f"{c.count()} commits indexed")
```

### Check Codex MCP config (read-only)
Read `~/.codex/config.toml` with Python 3.11's TOML parser and report only whether the server entry exists; never print its configuration values.
```bash
python3 -c 'from pathlib import Path; import tomllib; p=Path.home()/".codex/config.toml"; d=tomllib.loads(p.read_text(encoding="utf-8")) if p.is_file() else {}; print("claude-memory configured" if "claude-memory" in d.get("mcp_servers", {}) else "claude-memory not configured")'
```

### Check hook
```bash
ls -la /path/to/repo/.git/hooks/post-commit
cat /path/to/repo/.git/hooks/post-commit | head -5
```

### Check Ollama is running (required for local mode)
```bash
curl -s http://localhost:11434/api/tags | python3 -c "import sys,json; print([m['name'] for m in json.load(sys.stdin).get('models',[])])"
```

## Healthy Status Example

```
── claude-memory status ──────────────────────────
  Repo          : lokumcu
  Chroma docs   : 39
  Total commits : 42
  Coverage      : 93%
```

## Common Issues

| Symptom | Fix |
|---------|-----|
| `0 commits indexed` | Run `claude-memory index --repo-path .` |
| MCP tools return errors | Check Ollama is running: `ollama serve` |
| Hook not firing | `chmod +x .git/hooks/post-commit` |
| Wrong user-id | Must match `CLAUDE_MEMORY_USER_ID` in MCP config |
| Chroma path conflict | Ensure `CLAUDE_MEMORY_CHROMA_DIR` is set to `chroma_commits/` (not `chroma/` used by Mem0) |

## Codex Runtime

Keep `claude-memory` as the external product name. Use its actual MCP tools when available; otherwise preflight and use the `claude-memory` CLI.

Never expose or print secret, credential, or token values.

Mandatory dependencies:
- `claude-memory CLI or MCP`
- `local claude-memory services`

Preflight each dependency using MCP/app capability discovery, CLI availability/version checks, read-only filesystem or Git checks for repositories, and provider auth-status commands without printing secrets, credentials, or tokens.
If any mandatory dependency is unavailable, stop and report a concise blocked state naming the missing dependency and the next action needed.
