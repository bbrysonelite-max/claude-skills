# Codex Skills Validation

- **Observed date:** 2026-07-14
- **Structural fingerprint:** `cc2ed81383a6eb2720f41b5367d44789cff92d1459a1b7dd99f97d6b25c33ac7`
- **Overall:** PASS
- **Collection:** 59 total; 6 native; 9 adapted; 44 dependency-required
- **Protected sources:** PASS; 241 files; snapshot SHA-256 `f3ca4bac9da5a321dcc3a87d63c0a486586dbf01bcbe8eb6f3f73c3284028e69`
- **Generated resources:** 97 Markdown; 279 total files
- **Runtime contracts:** 53 sections; 6 native absences; 44 dependency preflights; 44 no-secret clauses
- **Official validator:** 0/0 passed
- **Regression suites:** **NOT OBSERVED**
- **Injected defect checks:** **NOT OBSERVED**
- **Installability:** generated names and resources validated; personal installation not inspected

## Schema, Metadata, Runtime, and Resources

Structural/schema validation: **PASS**. Metadata, normalized output parity, Markdown compatibility, local links, symlink containment, helper overlays, resource modes, and runtime contracts were checked from generated files.

## Official Validator Execution

Official validator execution was not observed.

## Regression and Injection Evidence

Regression suites: **NOT OBSERVED**.

Injected defect checks: **NOT OBSERVED**.

## Syntax Checks

| Language | Observed files | Interpreters | Result |
|---|---:|---|---|
| python | 0 | not available | PASS |
| shell | 0 | not available | PASS |
| javascript | 0 | not available | PASS |

Python resources were compiled with the default `python3` and Python 3.11 when available. Shell resources used `bash -n`; JavaScript resources used `node --check` when Node was available. Fixtures, caches, vendored trees, and build outputs were excluded.

## Immediately Usable and Adapted

The native and adapted skills below have no mandatory external dependency contract in the manifest:

`agent-reach`, `ai-evaluation-audit`, `allsup-leads-ssdi`, `allsup-leads-veterans`, `assumptions-audit`, `blind-spots-audit`, `blueprint`, `claude-memory-debug`, `claude-memory-index`, `claude-memory-search`, `claude-memory-status`, `closing-ritual`, `cloud-run-reauth`, `codebase-pattern-mapping`, `context-keeper`, `desktop-delivery`, `doc-keeper`, `documentation-claim-verification`, `failure-modes`, `gitnexus-cli`, `gitnexus-debugging`, `gitnexus-exploring`, `gitnexus-guide`, `gitnexus-impact-analysis`, `gitnexus-pr-review`, `gitnexus-refactoring`, `graphify`, `ground-truth`, `gws-shared`, `gws-workflow`, `gws-workflow-email-to-task`, `gws-workflow-file-announce`, `gws-workflow-meeting-prep`, `gws-workflow-standup-report`, `gws-workflow-weekly-digest`, `here-now`, `integration-flow-audit`, `intro-page`, `last30days`, `mine`, `network-reactivator`, `page-rethink`, `production-gate-audit`, `refine`, `requirements-coverage-audit`, `ship-it`, `signal-mine`, `skill-miner`, `skills-librarian`, `the-rebuild`, `threat-mitigation-audit`, `tiger-doc-keeper`, `tiger-leader-hunt`, `tiger-whitepaper`, `tigerclaw-daily-checks`, `truth-keeper`, `two-brents-brand`, `vault-hygiene`, `whitelabel-radar`

## Dependency-Gated Skills

Statuses are non-secret observations only. Connector-dependent does not claim that a connector is available.

| Skill | Exact mandatory dependencies | Observed preflight status |
|---|---|---|

## Personal Installation

Personal migration is pending. No personal skill was changed by this source-sync validation. The established migration command remains `python3 scripts/install.py --exclude last30days`, preserving the personal `last30days` installation.

## Limitations

No live external workflows, external services, credentials, production commands, or user media were executed. Availability checks do not expose credential values and do not prove live connector authorization.
