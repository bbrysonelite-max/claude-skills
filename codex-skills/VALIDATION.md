# Codex Skills Validation

- **Observed date:** 2026-07-13
- **Structural fingerprint:** `9c1d615e15995c12f686352ec2eb06c170300e2d8069506255385acc595d2709`
- **Overall:** PASS
- **Collection:** 58 total; 6 native; 12 adapted; 40 dependency-required
- **Protected sources:** PASS; 238 files; snapshot SHA-256 `75cb6068de4998477b8ecf7902a8ae2b98f16871406582d89c84ef944b7adccd`
- **Generated resources:** 88 Markdown; 268 total files
- **Runtime contracts:** 52 sections; 6 native absences; 40 dependency preflights; 40 no-secret clauses
- **Official validator:** 58/58 passed
- **Regression suites:** **PASS**
- **Injected defect checks:** **PASS**; 9/9 detected
- **Installability:** generated names and resources validated; personal installation not inspected

## Schema, Metadata, Runtime, and Resources

Structural/schema validation: **PASS**. Metadata, normalized output parity, Markdown compatibility, local links, symlink containment, helper overlays, resource modes, and runtime contracts were checked from generated files.

## Official Validator Execution

Observed execution modes: `offline-cached` 57, `offline-cached-fallback` 1.
Initial online diagnostic (sanitized): uv PyYAML dependency resolution failed because DNS lookup failed.
Fallback evidence: online dependency resolution failed, then the cached `UV_OFFLINE=1` environment validated 58/58 skills.

## Regression and Injection Evidence

| Interpreter | Observed tests | Result |
|---|---:|---|
| Python 3.14.5 | 219/219 | PASS |
| Python 3.11.15 | 219/219 | PASS |

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

## Limitations

No live external workflows, external services, credentials, production commands, or user media were executed. Availability checks do not expose credential values and do not prove live connector authorization.
