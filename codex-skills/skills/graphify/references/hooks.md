# graphify reference: commit hook and Codex integration

Load this when the user asks to install the post-commit hook or make graphify part of a Codex project workflow.

## For git commit hook

Install a post-commit hook that rebuilds the graph after every commit. No background process is required.

```bash
graphify hook install    # install
graphify hook uninstall  # remove
graphify hook status     # check
```

After every `git commit`, the hook detects changed code files with `git diff HEAD~1`, reruns AST extraction, and rebuilds `graph.json` and `GRAPH_REPORT.md`. Doc or image changes are ignored by the hook; run `$graphify --update` for those.

If a post-commit hook already exists, graphify appends to it rather than replacing it.

## For Codex project integration

Do not run product-specific commands that write another agent's instruction file. Add graphify guidance to the project's `AGENTS.md` only after the user approves that edit. The guidance should tell Codex to query an existing `graphify-out/graph.json` before broad codebase exploration and to run `graphify update` after relevant code changes.
