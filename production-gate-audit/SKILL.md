---
name: production-gate-audit
description: Use when auditing a project for production readiness, preparing a repo for solo-founder AI-assisted development, adding CI/branch-protection enforcement, verifying Stripe/webhook safety, tenant isolation, connector validation, or deciding which tests are missing or weak. Builds ONE clean production gate covering 10 unique risks — no duplicate coverage, no cosmetic tests. Audit and enforcement only, not a feature-building skill.
---

# Production Gate Audit

Audit an existing software project and determine whether it is safe for solo-founder, AI-assisted production development.

The skill checks whether the project has **one clean production gate** covering ten unique risks:

1. Repo protection
2. CI build gate
3. Security gate
4. Health check
5. Auth
6. Tenant isolation
7. Payment / webhook safety
8. Connector validation
9. E2E customer path
10. Deployment / rollback proof

The goal is NOT many overlapping tests. The goal is one straightforward production-quality test and security gate with no duplication and no double coverage.

**Announce at start:** "I'm using the production-gate-audit skill to audit this project's production gate."

## Core Rule

One gate. Ten checks. Each check covers one unique production risk.

- No duplicate coverage.
- No cosmetic tests.
- No scorecard sprawl.
- No merge unless the gate passes.

## When To Use

Use when:
- auditing an existing project
- preparing a repo for AI-assisted development
- adding enforcement to a production codebase
- checking whether tests are meaningful
- preparing GitHub branch protection and CI gates
- deciding what tests are missing
- verifying Stripe/webhook safety
- verifying tenant isolation
- verifying connector validation
- creating a production readiness report

Do NOT use this skill to build new features. This is an audit and enforcement skill.

## Inputs To Inspect

- `package.json`
- existing test folders
- existing GitHub workflows
- branch protection status, if accessible
- security settings, if accessible
- health endpoint, if present
- auth routes/middleware
- tenant isolation logic
- Stripe/payment/webhook handlers
- connector validation routes/services
- E2E tests
- deployment config
- rollback docs
- `AGENTS.md`, `SACRED_WIRING.md`, `README.md`, `SOTU.md`, `NEXT_SESSION.md`

## Forbidden Without Explicit Approval

Do not casually modify:
- Stripe checkout logic
- Stripe webhook logic
- auth/session logic
- tenant isolation logic
- database migrations
- production environment variable names
- deployment configuration
- AI agent core behavior
- messaging connector behavior
- customer data schemas

If one of these must be touched, stop and report why.

## Workflow

### Phase 1 — Inspect Before Editing

Do not write code first. Inspect and report:

```txt
Package manager:
Test framework:
Build command:
Typecheck command:
Lint command:
Existing CI workflows:
Existing security workflows:
Existing test folders:
Existing E2E tests:
Existing health endpoint:
Existing auth tests:
Existing tenant isolation tests:
Existing webhook tests:
Existing connector tests:
Existing rollback docs:
```

### Phase 2 — Map Existing Coverage To The One Gate

Create this table using exactly the 10 gate areas (no extra categories unless absolutely necessary):

```txt
Gate Area | Existing Coverage | Strong Enough? | Missing Piece | Priority
```

### Phase 3 — Identify Duplicate Or Weak Tests

Call out:
- Duplicate / overlapping tests
- Snapshot-only critical tests
- Tests with no meaningful assertion
- Tests that mock the thing they claim to prove
- Tests that only check rendering
- Skipped tests
- Tests that cannot fail
- Tests that pass without hitting real logic

A test is weak if it would not catch a production failure.

### Phase 4 — Assign Priority

```txt
P0 — Must fix before production
P1 — Must fix before scaling customers
P2 — Useful hardening
P3 — Nice to have
```

P0 includes: main not protected; CI not running; build not checked; secrets exposed; auth not tested; tenant isolation not tested; payment/webhook not tested if money is involved; no health check; no rollback path.

### Phase 5 — Implement Only Missing Pieces

Only after the audit, implement missing pieces:
1. Do not duplicate existing tests.
2. Do not create multiple competing gates.
3. Prefer one clear test per critical risk.
4. Prefer behavior tests over implementation tests.
5. Do not add cosmetic tests.
6. Do not weaken tests to make them pass.
7. Do not mock away the real risk.
8. Do not modify production code unless required for testability.
9. If production code must change, explain before changing it.
10. Keep the diff small.

## The One Production Gate

A PR may merge only when these pass.

### 1. Repo Protection
Prove: main branch protected; PR required; status checks required; direct pushes blocked; force pushes blocked; production deploy only from main.
Pass: No code can reach production without PR + passing checks.

### 2. CI Build Gate
Prove: typecheck passes; lint passes; tests pass; build passes.
Preferred command: `pnpm gate` or `npm run gate`.

Minimum package script (adjust package manager and build command to the repo):
```json
{
  "scripts": {
    "typecheck": "tsc --noEmit",
    "lint": "eslint .",
    "test": "vitest run",
    "build": "next build",
    "gate": "pnpm typecheck && pnpm lint && pnpm test && pnpm build"
  }
}
```

### 3. Security Gate
Prove: secret scanning enabled; push protection enabled; Dependabot enabled; dependency review enabled; CodeQL enabled; no raw secrets in code, logs, docs, tests, screenshots, or PR comments; no high-severity dependency issue.

### 4. Health Check
Prove: `GET /health` returns 200; response includes git SHA, region, and timestamp.
```json
{ "ok": true, "service": "api", "sha": "git-sha", "region": "us-central1", "time": "2026-05-26T00:00:00.000Z" }
```

### 5. Auth
Prove: unauthenticated request returns 401; valid auth returns 200; wrong role returns 403, if roles exist.
Pass: No private route can be accessed without valid auth.

### 6. Tenant Isolation
Prove: Tenant A cannot read / mutate / trigger-agent-of / access payment-order-log-state-of Tenant B.
Pass: Cross-tenant access fails every time.

### 7. Payment / Webhook Safety
Prove: checkout creates correct pending state; invalid webhook signature rejected; valid signed webhook updates state; duplicate event ID processes once; failed/expired payment does not activate account; refund/cancel updates state safely.
Pass: No fake webhook works. No duplicate webhook double-activates or double-writes.

### 8. Connector Validation
Prove: invalid connector credentials rejected; valid accepted; connector failure returns safe error; raw secrets never returned to frontend; tenant cannot activate until required connectors validate.
Connectors: Telegram, LINE, WhatsApp, SMS, Email, Cal.com, OpenAI / OpenRouter / model provider.

### 9. E2E Customer Path
Prove the real customer path: new user reaches signup/onboarding/wizard; required setup validates; agent reaches ready state; first message/reply path works.
Keep to one meaningful E2E test unless the project truly needs more.

### 10. Deployment / Rollback Proof
Prove: staging/preview tested; logs checked; uptime monitor active on /health; post-deploy probe runs; rollback command documented; previous commit known; migration rollback known, if relevant; incident/postmortem template exists.
Pass: The deploy can be observed and reversed.

## Required Output Format — Audit Report

```md
# Production Gate Audit Report

## Verdict
Pass / Partial / Fail

## Summary
One paragraph.

## Gate Table
| # | Gate Area | Status | Evidence | Gap | Priority |
|---|---|---|---|---|---|
| 1 | Repo protection |  |  |  |  |
| 2 | CI build gate |  |  |  |  |
| 3 | Security gate |  |  |  |  |
| 4 | Health check |  |  |  |  |
| 5 | Auth |  |  |  |  |
| 6 | Tenant isolation |  |  |  |  |
| 7 | Payment / webhook safety |  |  |  |  |
| 8 | Connector validation |  |  |  |  |
| 9 | E2E customer path |  |  |  |  |
| 10 | Deployment / rollback proof |  |  |  |  |

## Duplicate Or Weak Tests Found
## P0 Fixes Required
## P1 Fixes Recommended
## Files Inspected
## Files Changed
## Commands Run
Paste exact commands and results.
## Current Gate Command
## CI Status
## Remaining Risk
## Rollback Instructions
```

## Implementation Output Format

If implementing missing pieces, output:

```md
# Production Gate Implementation Report

## Summary
## What Was Added
## What Was Not Added
## Existing Tests Reused
## Duplicate Tests Avoided
## Files Changed
## Commands Run
## Results
## Gate Status
Pass / Partial / Fail
## Remaining Gaps
## Rollback
```

## Stop Conditions

Stop and ask for approval if: Stripe logic must change; auth/session logic must change; tenant isolation logic must change; database migration is needed; deployment config must change; environment variable names must change; AI agent core behavior must change; test requires real production credentials; test would expose secrets; repo structure is unclear.

## Quality Bar

Successful when: the repo has one gate command; CI runs the gate; the 10 production risks are each covered once; no duplicate test suites; no cosmetic tests; no sacred wiring changed casually; the report clearly says what is safe, what is missing, and what remains risky.

## Final Principle

Do not optimize for number of tests. Optimize for confidence that production cannot silently break.
