---
name: threat-mitigation-audit
description: Use when a declared threat model or risk register needs evidence that each recorded disposition and mitigation is implemented before release.
---

# Threat Mitigation Audit

Verify declared threats against implementation and disposition evidence. This is not a generic vulnerability scan.

## Codex Runtime

Operate directly in the main Codex agent. Keep the audit read-only and run only safe, non-mutating checks. No special credentials or external services are required. Never print, log, or expose secret values.

## Inputs and Preflight

- Obtain the declared threat model or risk register, including threat IDs, dispositions, planned mitigations, owners, and acceptance or transfer records.
- Obtain the repository root, target revision, and approved verification commands.
- Confirm that each declared threat has enough detail to identify the expected control or disposition evidence.
- If there is no declared threat set, stop; do not replace it with an open-ended security scan.

## Workflow

1. Normalize every declared threat into `ID`, asset or boundary, scenario, disposition, expected mitigation or record, and consequence.
2. Assume each mitigation or disposition is absent until evidence proves otherwise. Plans and threat-model prose are intent, not implementation.
3. For mitigation dispositions, trace the control through the actual request, data, or execution path and run focused verification where safe.
4. For accepted threats, verify the explicit acceptance record, scope, owner, rationale, review date, and residual risk.
5. For transferred threats, verify the transfer record, responsible external party, covered scope, enforceable contract or control, and remaining internal duties.
6. Assign exactly one status:
   - **VERIFIED:** the declared mitigation is implemented in the relevant path and supported by executable or direct evidence.
   - **ACCEPTED:** explicit, current acceptance evidence covers the declared threat and residual risk.
   - **TRANSFERRED:** explicit, current transfer evidence covers the declared threat and names retained responsibilities.
   - **OPEN:** evidence is absent, incomplete, contradicted, stale, or does not cover the actual path.
7. Prioritize OPEN threats by impact, exploitability, reachability, and missing-control breadth.

## Evidence Rules

- Cite threat declarations, controls, tests, and records as `path:line`; cite commands with decisive output.
- Label an **Observed fact** only when directly supported by implementation, run, or disposition evidence.
- Label an **Inference** when evidence suggests coverage but cannot prove it; inference cannot close a threat.
- Label **Unverifiable** when required implementation or disposition evidence is inaccessible; keep the status OPEN.
- File, dependency, or control-name existence alone does not verify mitigation.

## Stop and Error Conditions

- Stop before exploit attempts, destructive probes, credential use, or live-system checks not explicitly approved.
- Do not change code, mitigations, tests, threat records, or disposition documents.
- Report malformed or conflicting threat entries without inventing the intended disposition.

## Output Contract

Return:

1. Scope, declared threat count, evidence inspected, and checks run.
2. A table with `Threat ID`, `Disposition`, `Expected evidence`, `Status`, `Observed evidence`, and `Residual gap`.
3. OPEN threats first, prioritized with concrete consequence and required mitigation or disposition proof.
4. VERIFIED, ACCEPTED, and TRANSFERRED totals plus unresolved and unverifiable items.
5. A release recommendation grounded only in declared threats, with confirmation that no code changed.
