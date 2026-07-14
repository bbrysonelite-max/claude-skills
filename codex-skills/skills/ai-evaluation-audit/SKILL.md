---
name: "ai-evaluation-audit"
description: "Use when an implemented AI feature needs its planned evaluation dimensions, guardrails, and evaluation infrastructure checked before deployment."
---

# AI Evaluation Audit

Compare the planned evaluation strategy with code and actual runs, then issue a transparent deployment verdict.

## Codex Runtime

Operate directly in the main Codex agent. Keep the audit read-only and use safe repository inspection and evaluation commands. No special credentials or external services are required. Never print, log, or expose secret values.

## Inputs and Preflight

- Obtain the planned eval dimensions, rubrics, weights, guardrails, datasets, infrastructure, release thresholds, and target implementation revision.
- Obtain the repository root and executable eval or test commands.
- Identify which evaluations are offline, online, human-reviewed, model-judged, or environment-dependent.
- If no evaluation plan exists, stop scoring and return NOT IMPLEMENTED with the missing planning inputs.

## Workflow

1. Extract every planned eval dimension and its success criteria. Include quality, safety, reliability, latency, cost, fairness, domain-specific behavior, and regression controls when declared.
2. Trace each dimension to implemented evaluators, datasets, rubrics, assertions, and recorded runs. Documentation and metric logging alone do not prove evaluation.
3. Score each dimension:
   - **COVERED:** implementation targets the rubric behavior and executable evidence meets the planned threshold.
   - **PARTIAL:** relevant implementation exists but its rubric, data, automation, execution, or threshold proof is incomplete.
   - **MISSING:** no implementation directly evaluates the planned dimension.
4. Audit planned guardrails in the actual request and response paths. A declared but bypassed, stubbed, or untested guardrail is MISSING.
5. Audit infrastructure: tooling is invoked, datasets meet the declared composition, CI runs the evaluation, tracing wraps actual AI calls, and results affect release decisions where planned.
6. Run safe evaluations and record exact results. Separate code presence from run proof and current results from historical reports.
7. Calculate a weighted score using declared weights. If weights are absent, use equal weights and state that choice. Use COVERED = 1, PARTIAL = 0.5, and MISSING = 0; show every term and the total.
8. Apply declared deployment thresholds. Regardless of score, any MISSING critical dimension or guardrail produces DO NOT DEPLOY. Do not soften MISSING to PARTIAL because adjacent tests exist.

## Evidence Rules

- Cite plans, evaluators, datasets, guardrails, and CI as `path:line`; cite runs with command, result, and decisive output.
- Label an **Observed fact** only when code or a run directly establishes it.
- Label an **Inference** when evidence suggests coverage but misses direct rubric or execution proof; inference cannot earn COVERED.
- Label **Unverifiable** when required data, environment, judge, or run history is unavailable; explain its effect on status and verdict.
- Do not credit planned artifacts as implemented evaluation evidence.

## Stop and Error Conditions

- Stop before evaluations that expose private data, reveal credentials, incur unapproved cost, mutate production, or call unapproved live services.
- Do not change code, datasets, prompts, guardrails, tests, or CI configuration.
- If an evaluation command fails, distinguish evaluator failure, product failure, and environment failure; preserve partial results without improving the status.

## Output Contract

Return:

1. A dimension table with `Dimension`, `Weight`, `Planned rubric`, `Implementation and run evidence`, `Status`, and `Gap`.
2. A guardrail and infrastructure table covering tooling, datasets, CI, online paths, tracing, and release integration.
3. COVERED, PARTIAL, and MISSING totals plus the complete weighted calculation.
4. Critical gaps and concrete remediation, ordered by deployment risk.
5. A deploy verdict of READY, NEEDS WORK, or DO NOT DEPLOY, grounded in code and runs with no softening.
6. Unverifiable items, skipped commands, and confirmation that no code changed.
