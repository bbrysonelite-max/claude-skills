---
name: ship-it
description: Take a TigerClaw PR from green to live — watch CI to completion, merge on Brent's explicit per-PR approval, verify the merge landed (state MERGED + merged SHA), watch the Cloud Run deploy, and verify the live api.tigerclaw.io/health gitSha matches the merged SHA. Reports a timestamped GO / PARTIAL verdict. Use when Brent says "ship it", "merge and verify", "merge <PR#>", "watch CI then merge", "verify the deploy", "is it live", "verify health after deploy", or asks to take a PR to production. Encodes his rules: never push to main, verify MERGED, inspect the merged SHA's deploy (not the PR-head rollup), live health check, timestamp everything UTC.
---

# ship-it

The merge → CI-watch → Cloud Run deploy → live `/health` loop Brent runs on nearly every PR.
A deterministic script does the mechanical parts; you own the **approval gate** and the verdict.

## Hard rules (non-negotiable — from AGENTS.md / CLAUDE.md)

- **Never merge without Brent's explicit OK for THAT PR.** The script refuses to merge without `--confirm`; you supply it only after he says go for that specific PR number.
- **Never push directly to main.** ship-it only merges existing PRs via `gh`.
- **Verify, don't assume.** A PR that was green before merge can still fail its post-merge deploy — that makes the closeout **PARTIAL**, not done.
- **Timestamp everything in UTC** (the script does). Never report "just now" / "earlier" as proof.
- If an earlier note overclaimed (e.g. "shipped"), correct the same record once the deploy/health truth is in.

## Workflow

1. **Confirm CI is green** (read-only):
   `bash scripts/ship-it.sh checks <PR#>`
   Watches the PR's checks to completion and prints the rollup. If anything required is failing, stop — fix first.
2. **Get Brent's explicit approval** to merge this PR. Do not skip. (His standing rule is per-PR approval.)
3. **Merge + verify merge** (mutating — only after step 2):
   `bash scripts/ship-it.sh merge <PR#> --confirm`
   Merges (squash, deletes branch), then confirms `state == MERGED` and captures the merged SHA. Aborts loudly if state isn't MERGED.
4. **Watch deploy + verify live** (read-only):
   `bash scripts/ship-it.sh deploy <PR#>`
   Resolves the merge SHA FRESH from the PR (never a cached value — a stale cache produced a false "LIVE" on 2026-07-20), waits for THAT SHA's `deploy.yml` run, polls `api.tigerclaw.io/health` until `build.gitSha` matches **and** `status == ok`, and — if the PR diff contains migrations — requires the "Successfully applied" line in prod logs. GO prints only on the full chain; it appends the MERGE_LEDGER line and posts it as a PR comment.
5. **Report the verdict** in your own words: GO (merged SHA live + health ok, with the UTC timestamp) or **PARTIAL** (merged but deploy failed / SHA mismatch / health not ok). Note that the **worker revision can lag** the api deploy — if the change is worker-side, confirm the worker too before calling it done.
6. **Hand off the doc update.** ship-it does not edit docs. If this closes work, remind Brent (or invoke `doc-keeper` / `truth-keeper`) to log the deploy in VERIFIED.md / SOTU.

## One-shot

`bash scripts/ship-it.sh full <PR#> --confirm` runs checks → merge → deploy in sequence
(still needs `--confirm`). Omit `--confirm` to run checks only and stop for approval.

## Config (env overrides, defaults are correct for prod)

`SHIP_IT_HEALTH_URL` (api.tigerclaw.io/health) · `SHIP_IT_DEPLOY_WORKFLOW` (deploy.yml) ·
`SHIP_IT_REPO_DIR` (~/tiger-claw-v4-core) · `SHIP_IT_MERGE_METHOD` (squash) ·
`SHIP_IT_POLL_TRIES` (24) · `SHIP_IT_POLL_SLEEP` (15s).

Requires `gh` (authed) and `python3`. See the script for exit codes (2 = no --confirm, 5 = not MERGED, 6 = health timeout).
