# Codex Skills Validation

- **Observed date:** 2026-07-13
- **Structural fingerprint:** `599e0eeaac9f06ac2cf0ed9094dadb5bee7fbc83b6178ce74f6a568749874f6c`
- **Overall:** PASS
- **Collection:** 58 total; 6 native; 12 adapted; 40 dependency-required
- **Protected sources:** PASS; 238 files; snapshot SHA-256 `75cb6068de4998477b8ecf7902a8ae2b98f16871406582d89c84ef944b7adccd`
- **Generated resources:** 88 Markdown; 268 total files
- **Runtime contracts:** 52 sections; 6 native absences; 40 dependency preflights; 40 no-secret clauses
- **Official validator:** 58/58 passed
- **Regression suites:** **PASS**
- **Injected defect checks:** **PASS**; 9/9 detected
- **Installability:** **PASS**; 57 managed links; 0 approved existing directories; 1 excluded (`last30days`); 58/58 generated names accounted for

## Schema, Metadata, Runtime, and Resources

Structural/schema validation: **PASS**. Metadata, normalized output parity, Markdown compatibility, local links, symlink containment, helper overlays, resource modes, and runtime contracts were checked from generated files.

## Official Validator Execution

Observed execution modes: `offline-cached` 57, `offline-cached-fallback` 1.
Initial online diagnostic (sanitized): uv PyYAML dependency resolution failed because DNS lookup failed.
Fallback evidence: online dependency resolution failed, then the cached `UV_OFFLINE=1` environment validated 58/58 skills.

## Regression and Injection Evidence

| Interpreter | Observed tests | Result |
|---|---:|---|
| Python 3.14.5 | 289/289 | PASS |
| Python 3.11.15 | 289/289 | PASS |

| Injected defect category | Exact injected defect | Detection | Result |
|---|---|---|---|
| Claude runtime compatibility | `Claude Code session environment` | detected | PASS |
| Claude runtime compatibility | `Claude-only tool` | detected | PASS |
| frontmatter and metadata | `extra frontmatter field` | detected | PASS |
| frontmatter and metadata | `missing default prompt token` | detected | PASS |
| local resource integrity | `missing inline script` | detected | PASS |
| local resource integrity | `broken Markdown link` | detected | PASS |
| resource syntax | `invalid py syntax` | detected | PASS |
| resource syntax | `invalid sh syntax` | detected | PASS |
| resource syntax | `invalid js syntax` | detected | PASS |

## Syntax Checks

| Language | Observed files | Interpreters | Result |
|---|---:|---|---|
| python | 80 | Python 3.11.15 (/Users/brentbryson/.local/bin/python3.11)<br>Python 3.14.5 (/usr/local/bin/python3) | PASS |
| shell | 12 | GNU bash, version 3.2.57(1)-release (x86_64-apple-darwin25) (/bin/bash) | PASS |
| javascript | 1 | v25.2.1 (/usr/local/bin/node) | PASS |

Python resources were compiled with the default `python3` and Python 3.11 when available. Shell resources used `bash -n`; JavaScript resources used `node --check` when Node was available. Fixtures, caches, vendored trees, and build outputs were excluded.

## Immediately Usable and Adapted

The native and adapted skills below have no mandatory external dependency contract in the manifest:

`ai-evaluation-audit`, `assumptions-audit`, `blind-spots-audit`, `blueprint`, `codebase-pattern-mapping`, `context-keeper`, `desktop-delivery`, `documentation-claim-verification`, `failure-modes`, `ground-truth`, `integration-flow-audit`, `network-reactivator`, `requirements-coverage-audit`, `skill-miner`, `skills-librarian`, `the-rebuild`, `threat-mitigation-audit`, `two-brents-brand`

## Dependency-Gated Skills

Statuses are non-secret observations only. Connector-dependent does not claim that a connector is available.

| Skill | Exact mandatory dependencies | Observed preflight status |
|---|---|---|
| `agent-reach` | `agent-reach CLI and platform backends` (connector-dependent) | connector-dependent |
| `allsup-leads-ssdi` | `Datamine environment` (connector-dependent)<br>`last30days data-source credentials` (credential-dependent)<br>`here.now publishing credentials` (credential-dependent) | credential-dependent |
| `allsup-leads-veterans` | `Datamine environment` (connector-dependent)<br>`last30days data-source credentials` (credential-dependent)<br>`here.now publishing credentials` (credential-dependent) | credential-dependent |
| `claude-memory-debug` | `claude-memory CLI or MCP` (connector-dependent)<br>`indexed Git repository` (connector-dependent) | connector-dependent |
| `claude-memory-index` | `claude-memory CLI or MCP` (connector-dependent)<br>`Git repository` (connector-dependent) | connector-dependent |
| `claude-memory-search` | `claude-memory CLI or MCP` (connector-dependent)<br>`indexed Git repository` (connector-dependent) | connector-dependent |
| `claude-memory-status` | `claude-memory CLI or MCP` (connector-dependent)<br>`local claude-memory services` (connector-dependent) | connector-dependent |
| `closing-ritual` | `target Git repository` (connector-dependent)<br>`repository test toolchain` (connector-dependent) | connector-dependent |
| `cloud-run-reauth` | `gcloud CLI` (available)<br>`Google Cloud user and ADC access` (credential-dependent)<br>`cloud-sql-proxy` (missing) | missing |
| `doc-keeper` | `target Git repository` (connector-dependent)<br>`repository documentation checks` (connector-dependent) | connector-dependent |
| `gitnexus-cli` | `GitNexus CLI or MCP` (connector-dependent)<br>`indexed Git repository` (connector-dependent) | connector-dependent |
| `gitnexus-debugging` | `GitNexus CLI or MCP` (connector-dependent)<br>`indexed Git repository` (connector-dependent) | connector-dependent |
| `gitnexus-exploring` | `GitNexus CLI or MCP` (connector-dependent)<br>`indexed Git repository` (connector-dependent) | connector-dependent |
| `gitnexus-guide` | `GitNexus CLI or MCP` (connector-dependent)<br>`indexed Git repository` (connector-dependent) | connector-dependent |
| `gitnexus-impact-analysis` | `GitNexus CLI or MCP` (connector-dependent)<br>`indexed Git repository` (connector-dependent) | connector-dependent |
| `gitnexus-pr-review` | `GitNexus CLI or MCP` (connector-dependent)<br>`Git repository and PR diff` (connector-dependent) | connector-dependent |
| `gitnexus-refactoring` | `GitNexus CLI or MCP` (connector-dependent)<br>`indexed Git repository` (connector-dependent) | connector-dependent |
| `gws-shared` | `connected Google Workspace apps or gws CLI` (connector-dependent)<br>`Google Workspace credentials` (credential-dependent) | credential-dependent |
| `gws-workflow` | `connected Google Workspace apps or gws CLI` (connector-dependent)<br>`Google Workspace credentials` (credential-dependent) | credential-dependent |
| `gws-workflow-email-to-task` | `connected Gmail and task apps or gws CLI` (connector-dependent)<br>`Google Workspace credentials` (credential-dependent) | credential-dependent |
| `gws-workflow-file-announce` | `connected Drive and Chat apps or gws CLI` (connector-dependent)<br>`Google Workspace credentials` (credential-dependent) | credential-dependent |
| `gws-workflow-meeting-prep` | `connected Gmail, Calendar, and Drive apps or gws CLI` (connector-dependent)<br>`Google Workspace credentials` (credential-dependent) | credential-dependent |
| `gws-workflow-standup-report` | `connected Google Calendar and Google Tasks capabilities or gws CLI` (connector-dependent)<br>`Google Workspace credentials` (credential-dependent) | credential-dependent |
| `gws-workflow-weekly-digest` | `connected Gmail, Calendar, and Drive apps or gws CLI` (connector-dependent)<br>`Google Workspace credentials` (credential-dependent) | credential-dependent |
| `here-now` | `bash` (available)<br>`curl` (available)<br>`file` (available)<br>`bundled or system jq` (not-probed)<br>`here.now network access` (connector-dependent) | partial |
| `intro-page` | `SSH website host access` (credential-dependent)<br>`browser automation` (connector-dependent) | credential-dependent |
| `last30days` | `Python 3.12 or newer` (available)<br>`public network access` (connector-dependent) | connector-dependent |
| `mine` | `Datamine repository and environment` (connector-dependent)<br>`last30days data-source credentials` (credential-dependent) | credential-dependent |
| `page-rethink` | `browser automation` (connector-dependent)<br>`target website repository` (connector-dependent) | connector-dependent |
| `production-gate-audit` | `target repository and deployment` (connector-dependent)<br>`production service credentials` (credential-dependent) | credential-dependent |
| `refine` | `Sherlock and blue-healer repositories` (not-probed)<br>`OSINT and enrichment credentials` (credential-dependent) | partial |
| `ship-it` | `tiger-claw-v4-core repository` (connector-dependent)<br>`deployment credentials` (credential-dependent) | credential-dependent |
| `signal-mine` | `source APIs and credentials` (credential-dependent)<br>`Python script dependencies` (not-probed) | partial |
| `tiger-doc-keeper` | `tiger-claw-v4-core repository` (connector-dependent)<br>`repository documentation checks` (connector-dependent) | connector-dependent |
| `tiger-leader-hunt` | `last30days skill and data-source credentials` (credential-dependent) | credential-dependent |
| `tiger-whitepaper` | `Node.js` (available)<br>`Google Chrome` (available) | available |
| `tigerclaw-daily-checks` | `tiger-claw-v4-core repository` (connector-dependent)<br>`gcloud and database credentials` (credential-dependent) | credential-dependent |
| `truth-keeper` | `local Truth directory` (connector-dependent)<br>`project repositories` (not-probed) | partial |
| `vault-hygiene` | `local Obsidian vault repository` (connector-dependent) | connector-dependent |
| `whitelabel-radar` | `last30days and tiger-leader-hunt skills` (not-probed)<br>`enrichment and publishing credentials` (credential-dependent) | partial |

## Personal Installation

- **Observed target/source:** `/Users/brentbryson/.codex/skills` from `/Users/brentbryson/.config/superpowers/worktrees/claude-skills/parallel-codex-skills/codex-skills/skills` on 2026-07-13.
- **Preflight:** `python3 codex-skills/scripts/validate.py --source-only --json` matched 238 protected source hashes; `python3 codex-skills/scripts/validate.py --check` validated 58 skills with 0 errors and 0 warnings. All 18 existing personal trees matched their captured path types and content digests.
- **Dry run:** `python3 codex-skills/scripts/install.py --dry-run --exclude last30days --json` reported 57 planned creates, 0 applied creates/updates, 1 exclusion, and 0 collisions/errors/warnings.
- **First install:** `python3 codex-skills/scripts/install.py --exclude last30days --json` reported 57 created, 0 updated/unchanged/skipped, 1 exclusion, and 0 collisions/errors/warnings after permission approval. The earlier sandbox-denied mutation attempt reported 0 created and left all 18 original trees unchanged with no debris.
- **Idempotence:** the same installer command reported 57 unchanged, 0 created/updated/skipped, 1 exclusion, and 0 collisions/errors/warnings.
- **Installed validation:** `python3 codex-skills/scripts/validate.py --installed /Users/brentbryson/.codex/skills --exclude last30days --json` passed with 57 managed links, 0 approved existing directories, 1 exclusion, 0 errors, and 0 warnings. Official validation passed 58/58 generated skills; both regression interpreters passed 289/289 tests.
- **Managed links:** all 57 are absolute direct links to tracked generated skill directories in the exact source worktree; every target resolves and contains `SKILL.md`.
- **Explicit exception:** `last30days` remains a real personal directory and was not inspected, validated, moved, replaced, edited, or counted as managed by the exclusion workflow. Its tree digest remained `e294507383b773c2372033750130fd1e747e8f75110293da26e328208c0259e5`; its `SKILL.md` SHA-256 `bee461995acc5faf1a9608d2f8c6ea82017995dc7b2bcf525f845331392cd5cf` matches the repository upstream source and intentionally differs from the generated Codex adaptation.
- **Preservation and cleanup:** all 17 unrelated pre-existing personal skill trees and excluded `last30days` retained their captured types and content digests. No stage, ready, backup, recovery, or `codex-install` debris remained.

## Limitations

No live external workflows, external services, credentials, production commands, or user media were executed. Availability checks do not expose credential values and do not prove live connector authorization.
