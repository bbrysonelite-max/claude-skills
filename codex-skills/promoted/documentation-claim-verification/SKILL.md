---
name: documentation-claim-verification
description: Use when documentation, release notes, runbooks, or status reports contain factual claims that need verification against current implementation and executable evidence.
---

# Documentation Claim Verification

Verify what documentation says, not merely whether referenced files exist.

## Codex Runtime

Operate directly in the main Codex agent. Work read-only unless the user explicitly requests a report file. No special credentials or external services are required. Never print, log, or expose secret values.

## Inputs and Preflight

- Obtain the documents to review, repository root, claimed version or revision, and any relevant verification commands.
- Establish whether each document describes current, historical, planned, or environment-specific behavior.
- Confirm referenced code and tests are locally inspectable.
- If the target revision or document scope cannot be determined, stop and report that limitation.

## Workflow

1. Extract checkable claims about behavior, interfaces, configuration, compatibility, test results, deployment state, or operational procedure. Separate opinions and future intent.
2. Normalize compound claims into independently verifiable statements.
3. Select the strongest verification method for each claim: exact code path, configuration value, schema, test assertion, or executable command.
4. Verify exact content and behavior, not mere existence. A file, symbol, or test name is insufficient unless its contents establish the claim.
5. Assign one status:
   - **PASS:** direct evidence confirms the complete claim.
   - **FAIL:** direct evidence contradicts all or part of the claim.
   - **UNVERIFIABLE:** necessary evidence is missing, inaccessible, or non-executable.
6. Classify impact:
   - **BLOCKER:** a FAIL or critical UNVERIFIABLE claim could cause unsafe use, broken integration, or an invalid release decision.
   - **WARNING:** the claim is incomplete, stale, or lower impact but still needs correction or evidence.
7. Aggregate results without allowing several minor PASS results to hide a blocker.

## Evidence Rules

- Cite document claims and implementation evidence as `path:line`; include exact commands and decisive output for run evidence.
- Label an **Observed fact** only when directly confirmed.
- Label an **Inference** when evidence requires interpretation; state the reasoning and do not convert it to PASS without proof.
- Label **Unverifiable** when proof cannot be obtained and name the missing evidence.
- Do not treat documentation as implementation evidence for its own claim.

## Stop and Error Conditions

- Stop a check when running it would mutate data, require undisclosed credentials, or target an unapproved live system.
- Do not edit code or documentation unless the user explicitly requests a report file; a report request authorizes only that file.
- Preserve partial results when one check fails and identify checks that were not run.

## Output Contract

Return:

1. A structured summary with PASS, FAIL, and UNVERIFIABLE totals plus BLOCKER and WARNING totals.
2. A claim table with `Claim`, `Document citation`, `Status`, `Implementation or run evidence`, `Impact`, and `Required correction`.
3. Blockers first, then warnings and verified claims.
4. Unrun checks and the evidence needed to resolve them.
5. The overall documentation reliability conclusion and whether a report file was written.
