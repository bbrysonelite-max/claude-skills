---
name: "codebase-pattern-mapping"
description: "Use when an unfamiliar repository or proposed change needs evidence-backed analogs, conventions, and integration points before design or implementation."
---

# Codebase Pattern Mapping

Map the repository patterns that should shape a proposed change. This is a read-only discovery workflow.

## Codex Runtime

Operate directly in the main Codex agent. Inspect the repository and run only non-mutating discovery or verification commands. No special credentials or external services are required. Never print, log, or expose secret values.

## Inputs and Preflight

- Obtain the proposed behavior, affected domain, and repository root.
- Identify relevant languages, frameworks, packages, entry points, and ownership boundaries.
- Confirm the checked-out code is sufficient to inspect; note generated, vendored, or inaccessible areas.
- If the requested behavior or repository boundary is unclear, stop and identify the ambiguity.

## Workflow

1. Locate the feature's likely entry points, data types, configuration, tests, and public interfaces.
2. Find the closest analogs by behavior and architectural role, not merely by similar names. Prefer current production paths over examples or dead code.
3. Trace each analog from entry point through core logic, persistence or external boundaries, and tests.
4. Record established conventions for naming, module placement, error handling, validation, state, dependencies, observability, and testing.
5. Identify integration points the change must use or preserve: callers, APIs, events, schemas, stores, feature flags, and lifecycle hooks.
6. Compare the proposed shape with the analogs. Call out deliberate deviations and explain their risks rather than silently normalizing them.
7. Rank the mapped patterns by relevance and evidence strength. Distinguish a dominant convention from isolated examples.

## Evidence Rules

- Cite every pattern and analog with `path:line`; include symbol names where useful.
- Label an **Observed fact** only when directly visible in current code, configuration, or tests.
- Label an **Inference** when several facts imply a convention; explain the connection.
- Label **Unverifiable** when generated code, external systems, or missing history prevents confirmation.
- File existence alone does not prove a pattern; cite the exact behavior or contract.

## Stop and Error Conditions

- Stop rather than inventing a convention when no close analog exists or relevant code is inaccessible.
- Do not change code, configuration, documentation, tests, or repository state.
- If examples conflict, report the conflict and evidence for each pattern.

## Output Contract

Return:

1. A concise repository and scope summary.
2. A ranked closest-analogs table with `Analog`, `Why it matches`, `Path citations`, and `Evidence strength`.
3. Conventions grouped by architecture, behavior, and tests.
4. Required integration points and boundary contracts.
5. Deliberate deviations, unresolved questions, and risks.
6. A suggested implementation shape grounded only in the mapped evidence, with confirmation that the audit was read-only.
