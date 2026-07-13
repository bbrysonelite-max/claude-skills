---
name: "requirements-coverage-audit"
description: "Use when requirements or acceptance criteria need traceability to tests and executable proof before work is declared complete."
---

# Requirements Coverage Audit

Measure whether tests prove required behavior, not whether test files merely exist.

## Codex Runtime

Operate directly in the main Codex agent. Audit without modifying the repository unless the user explicitly requests tests. No special credentials or external services are required. Never print, log, or expose secret values.

## Inputs and Preflight

- Obtain the authoritative requirements, acceptance criteria, repository root, and supported test commands.
- Establish requirement identifiers or assign stable audit IDs without rewriting the source requirements.
- Confirm the target revision and which test environments are available.
- If requirements are absent, contradictory, or not testable as written, stop and report those defects before scoring coverage.

## Workflow

1. Decompose each requirement into observable behaviors, including success, failure, boundary, authorization, and state-transition cases.
2. Locate candidate tests by behavior, symbols, fixtures, and commands rather than filenames alone.
3. Read exact assertions and setup. Distinguish test existence from behavior proof, and reject name-only matches.
4. Map every behavior to its strongest test and classify it:
   - **COVERED:** an executable test directly asserts the required behavior and passes.
   - **PARTIAL:** a test asserts only part of the behavior, relies on incomplete substitutes, or cannot be executed in the available environment.
   - **MISSING:** no test directly proves the behavior.
5. Run the narrowest relevant tests, then any safe broader suite needed to validate interactions. Record command, exit status, and decisive output.
6. Build a requirement-to-test matrix. Do not average away a critical MISSING behavior.
7. Prioritize gaps by requirement criticality, regression risk, and user impact.

## Evidence Rules

- Cite each requirement and assertion as `path:line`; cite executable test proof with command and result.
- Label an **Observed fact** only when source or run evidence directly establishes it.
- Label an **Inference** when a test appears relevant but does not directly assert the behavior; such evidence cannot earn COVERED.
- Label **Unverifiable** when a required test cannot be located or executed; explain whether the status is PARTIAL or MISSING.
- Passing unrelated suites and coverage percentages do not prove requirement coverage.

## Stop and Error Conditions

- Stop before tests that would mutate persistent data, require undisclosed credentials, or target an unapproved live system.
- Do not edit implementation or tests unless the user explicitly requests tests; an audit request alone is read-only.
- If execution is unavailable, complete the static matrix and mark the lack of executable proof explicitly.

## Output Contract

Return:

1. A requirement-to-test matrix with `Requirement`, `Behavior`, `Test and assertion`, `Run evidence`, `Status`, and `Gap`.
2. COVERED, PARTIAL, and MISSING totals, with critical gaps called out separately.
3. Commands run, results, and environment limitations.
4. A prioritized list of missing or incomplete tests without implementing them unless explicitly requested.
5. An overall coverage verdict and confirmation of whether any files changed.
