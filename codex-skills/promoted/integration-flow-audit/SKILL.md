---
name: integration-flow-audit
description: Use when completed work needs an evidence-backed audit of end-to-end user flows, component boundaries, data propagation, and failure paths before release.
---

# Integration Flow Audit

Trace complete user and system flows across boundaries and verify that their contracts work together.

## Codex Runtime

Operate directly in the main Codex agent. Keep the audit read-only and use repository inspection plus safe executable checks. No special credentials or external services are required. Never print, log, or expose secret values.

## Inputs and Preflight

- Obtain the intended user or end-to-end flows, relevant requirements, repository root, and available test commands.
- Identify participating components, runtime boundaries, external dependencies, and environment constraints.
- Confirm which checks are safe locally and which would touch live systems or persistent data.
- If no complete flow or expected outcome can be identified, stop and state what is missing.

## Workflow

1. Enumerate complete flows from trigger through final observable outcome. Include user actions, background work, callbacks, and asynchronous completion where applicable.
2. Trace every hop across UI, API, service, event, job, storage, and external boundaries.
3. At each hop, verify boundary contracts: request and response shapes, schemas, identifiers, ordering, retries, timeouts, and ownership.
4. Follow data propagation field by field. Check transformations, defaults, persistence, serialization, and whether the final consumer receives the intended value.
5. Trace error, auth, permission, state, cancellation, retry, and recovery paths. Include empty, stale, duplicate, and partially completed states where relevant.
6. Run the narrowest safe executable evidence first, then broader integration or end-to-end checks. Record skipped checks and why.
7. Compare execution results with static traces. Treat tests that execute only one component as boundary evidence, not complete-flow proof.
8. Produce prioritized findings by user impact, reachability, data risk, and recovery difficulty.

## Evidence Rules

- Cite code and tests as `path:line`; cite executable evidence with the exact command, result, and relevant output.
- Label an **Observed fact** only when a path or run directly demonstrates it.
- Label an **Inference** when control or data flow is deduced across files; explain the links.
- Label **Unverifiable** when a boundary, dependency, credentialed environment, or live state is unavailable.
- A passing unit test or existing route does not prove an end-to-end flow.

## Stop and Error Conditions

- Stop before any destructive, credential-revealing, or unapproved live-system check.
- Do not change code, tests, configuration, documentation, or data.
- If an executable check fails unexpectedly, preserve its output, continue independent traces, and distinguish product failure from environment failure.

## Output Contract

Return:

1. Scope, environments, commands run, and commands skipped.
2. A flow table with `Flow`, `Hops`, `Boundary contracts`, `Data propagation`, `Error/auth/state paths`, and `Evidence`.
3. Prioritized findings with severity, affected flow, exact break, evidence, and consequence.
4. Unverifiable boundaries and the proof needed to close them.
5. An overall integration verdict: complete, at risk, or blocked, with confirmation that no code was changed.
