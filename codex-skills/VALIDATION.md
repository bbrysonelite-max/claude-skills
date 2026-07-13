# Codex Skills Validation

- **Observed date:** 2026-07-13
- **Overall:** PASS
- **Collection:** 58 total; 6 native; 12 adapted; 40 dependency-required
- **Protected sources:** PASS; 238 files; snapshot SHA-256 `75cb6068de4998477b8ecf7902a8ae2b98f16871406582d89c84ef944b7adccd`
- **Generated resources:** 88 Markdown; 268 total files
- **Runtime contracts:** 52 sections; 6 native absences; 40 dependency preflights; 40 no-secret clauses
- **Official validator:** 58/58 passed
- **Installability:** generated names and resources validated; personal installation not inspected

## Schema, Metadata, Runtime, and Resources

Structural/schema validation: **PASS**. Metadata, normalized output parity, Markdown compatibility, local links, symlink containment, helper overlays, resource modes, and runtime contracts were checked from generated files.

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

Statuses are non-secret observations only. Connector/runtime-dependent does not claim that a connector is available.

| Skill | Exact mandatory dependencies | Observed preflight status |
|---|---|---|
| `agent-reach` | `agent-reach CLI and platform backends` | connector/runtime-dependent |
| `allsup-leads-ssdi` | `Datamine environment`<br>`last30days data-source credentials`<br>`here.now publishing credentials` | credential-dependent |
| `allsup-leads-veterans` | `Datamine environment`<br>`last30days data-source credentials`<br>`here.now publishing credentials` | credential-dependent |
| `claude-memory-debug` | `claude-memory CLI or MCP`<br>`indexed Git repository` | connector/runtime-dependent |
| `claude-memory-index` | `claude-memory CLI or MCP`<br>`Git repository` | connector/runtime-dependent |
| `claude-memory-search` | `claude-memory CLI or MCP`<br>`indexed Git repository` | connector/runtime-dependent |
| `claude-memory-status` | `claude-memory CLI or MCP`<br>`local claude-memory services` | connector/runtime-dependent |
| `closing-ritual` | `target Git repository`<br>`repository test toolchain` | connector/runtime-dependent |
| `cloud-run-reauth` | `gcloud CLI`<br>`Google Cloud user and ADC access`<br>`cloud-sql-proxy` | credential-dependent |
| `doc-keeper` | `target Git repository`<br>`repository documentation checks` | connector/runtime-dependent |
| `gitnexus-cli` | `GitNexus CLI or MCP`<br>`indexed Git repository` | connector/runtime-dependent |
| `gitnexus-debugging` | `GitNexus CLI or MCP`<br>`indexed Git repository` | connector/runtime-dependent |
| `gitnexus-exploring` | `GitNexus CLI or MCP`<br>`indexed Git repository` | connector/runtime-dependent |
| `gitnexus-guide` | `GitNexus CLI or MCP`<br>`indexed Git repository` | connector/runtime-dependent |
| `gitnexus-impact-analysis` | `GitNexus CLI or MCP`<br>`indexed Git repository` | connector/runtime-dependent |
| `gitnexus-pr-review` | `GitNexus CLI or MCP`<br>`Git repository and PR diff` | connector/runtime-dependent |
| `gitnexus-refactoring` | `GitNexus CLI or MCP`<br>`indexed Git repository` | connector/runtime-dependent |
| `gws-shared` | `connected Google Workspace apps or gws CLI`<br>`Google Workspace credentials` | credential-dependent |
| `gws-workflow` | `connected Google Workspace apps or gws CLI`<br>`Google Workspace credentials` | credential-dependent |
| `gws-workflow-email-to-task` | `connected Gmail and task apps or gws CLI`<br>`Google Workspace credentials` | credential-dependent |
| `gws-workflow-file-announce` | `connected Drive and Chat apps or gws CLI`<br>`Google Workspace credentials` | credential-dependent |
| `gws-workflow-meeting-prep` | `connected Gmail, Calendar, and Drive apps or gws CLI`<br>`Google Workspace credentials` | credential-dependent |
| `gws-workflow-standup-report` | `connected Google Calendar and Google Tasks capabilities or gws CLI`<br>`Google Workspace credentials` | credential-dependent |
| `gws-workflow-weekly-digest` | `connected Gmail, Calendar, and Drive apps or gws CLI`<br>`Google Workspace credentials` | credential-dependent |
| `here-now` | `bash`<br>`curl`<br>`file`<br>`bundled or system jq`<br>`here.now network access` | connector/runtime-dependent |
| `intro-page` | `SSH website host access`<br>`browser automation` | credential-dependent |
| `last30days` | `Python 3.12 or newer`<br>`public network access` | connector/runtime-dependent |
| `mine` | `Datamine repository and environment`<br>`last30days data-source credentials` | credential-dependent |
| `page-rethink` | `browser automation`<br>`target website repository` | connector/runtime-dependent |
| `production-gate-audit` | `target repository and deployment`<br>`production service credentials` | credential-dependent |
| `refine` | `Sherlock and blue-healer repositories`<br>`OSINT and enrichment credentials` | credential-dependent |
| `ship-it` | `tiger-claw-v4-core repository`<br>`deployment credentials` | credential-dependent |
| `signal-mine` | `source APIs and credentials`<br>`Python script dependencies` | credential-dependent |
| `tiger-doc-keeper` | `tiger-claw-v4-core repository`<br>`repository documentation checks` | connector/runtime-dependent |
| `tiger-leader-hunt` | `last30days skill and data-source credentials` | credential-dependent |
| `tiger-whitepaper` | `Node.js`<br>`Google Chrome` | available |
| `tigerclaw-daily-checks` | `tiger-claw-v4-core repository`<br>`gcloud and database credentials` | credential-dependent |
| `truth-keeper` | `local Truth directory`<br>`project repositories` | connector/runtime-dependent |
| `vault-hygiene` | `local Obsidian vault repository` | connector/runtime-dependent |
| `whitelabel-radar` | `last30days and tiger-leader-hunt skills`<br>`enrichment and publishing credentials` | credential-dependent |

## Limitations

No live external workflows, external services, credentials, production commands, or user media were executed. Availability checks do not expose credential values and do not prove live connector authorization.
