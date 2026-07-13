---
name: assumptions-audit
description: Use when a proposal, plan, or design needs its assumptions challenged against available evidence before implementation begins.
---

# Assumptions Audit

Identify consequential assumptions, test them against available evidence, and expose uncertainty before work begins. Do not implement the proposal.

## Codex Runtime

Operate directly in the main Codex agent. Keep the audit read-only and use repository inspection and non-mutating verification commands as evidence. No special credentials or external services are required. Never print, log, or expose secret values.

## Inputs and Preflight

- Obtain the proposal, plan, or design; its intended outcome; and the repository or artifacts it concerns.
- Identify explicit constraints, accepted facts, and decisions so they are not mislabeled as assumptions.
- Confirm that evidence can be inspected without changing implementation files.
- If the proposal is missing or too ambiguous to extract testable assumptions, stop and name the missing context.

## Workflow

1. Extract statements whose truth is necessary for the proposal to work. Include technical, product, operational, dependency, sequencing, and user-behavior assumptions.
2. Rewrite each assumption as a falsifiable statement. Merge duplicates, but do not hide distinct consequences.
3. Gather evidence for every assumption from code, configuration, tests, documentation, history, or command output. Absence of evidence is evidence of uncertainty, not confirmation.
4. Assign one confidence level:
   - **Confident:** direct, current evidence supports the assumption.
   - **Likely:** indirect or incomplete evidence supports it and no contradiction was found.
   - **Unclear:** evidence is absent, conflicting, stale, or inaccessible.
5. State the concrete consequence if wrong: rework, broken behavior, schedule risk, data loss, security exposure, or invalidated scope.
6. Separate gaps answerable inside the repository from gaps requiring external research, stakeholder input, live-system access, or experiments.
7. Prioritize assumptions by consequence and uncertainty. Surface high-consequence Unclear items first.

## Evidence Rules

- Cite repository evidence as `path:line`; cite command evidence with the exact command and decisive output.
- Label an **Observed fact** only when directly supported by inspected evidence.
- Label an **Inference** when evidence supports a conclusion but does not prove it; state the reasoning.
- Label **Unverifiable** when required evidence is unavailable; state what evidence would resolve it.
- Never use the proposal itself as evidence that its assumptions are true.

## Stop and Error Conditions

- Stop rather than guessing when referenced artifacts cannot be found, evidence access fails, or scope conflicts cannot be reconciled.
- Do not implement, edit code, rewrite the plan, or resolve assumptions on the user's behalf.
- Report partial progress and identify every assumption that could not be evaluated.

## Output Contract

Return:

1. A short scope and evidence summary.
2. A table with `ID`, `Assumption`, `Evidence`, `Confidence`, `Consequence if wrong`, and `Research gap`.
3. A prioritized list of high-consequence Unclear assumptions.
4. External-research and stakeholder questions, separated from repository-answerable gaps.
5. The overall readiness conclusion and a statement that no implementation was performed.
