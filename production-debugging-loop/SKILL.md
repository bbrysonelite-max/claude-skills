---
name: production-debugging-loop
description: >-
  Use when debugging any failure, regression, broken test, or production incident —
  including payment/Stripe bugs, webhook or queue/job failures, auth/session issues,
  tenant-isolation leaks, onboarding/wizard failures, UI regressions, or agent
  behavior bugs. Enforces a closed loop: no patch without evidence, no completion
  without proof, no serious bug closed without a regression guard. Especially for the
  Tiger / tiger-claw-v4-core codebase, where it adds money/tenant/webhook invariants.
---

# Production Debugging Loop

Debugging is a closed loop. The task is **not** done when the symptom disappears — it is
done when there is evidence the bug was understood, fixed, and guarded against returning.

```
Failure → Reproduce → Isolate → Hypothesize → Patch → Prove → Prevent → Record
```

Three standards, never waived:
- **No patch without evidence.**
- **No completion without proof.**
- **No serious bug closes without a regression guard.**

This skill defers to your other skills rather than duplicating them: use
`superpowers:test-driven-development` for writing the failing test, `superpowers:verification-before-completion`
before any "fixed" claim, `/investigate` for deep root-cause work, `/browse` or `/qa` to
capture UI proof, `/codex challenge` for the adversarial check, and `/ship` for the commit.

---

## Pick a mode (when in doubt, escalate to Serious)

| | **Small Bug Mode** | **Serious Bug Mode** |
|---|---|---|
| Use for | typos, labels, local styling, a broken import, harmless fixture | anything touching money, Stripe, refunds, auth, API keys, tenant isolation, messaging delivery, lead ownership, queue jobs, webhooks, onboarding, production data, permissions, deploys — or any bug where a wrong fix could leak data, duplicate work, lose money, or break trust |
| Loop | Reproduce → Patch → targeted test → report files + proof | Full 8-step procedure below |

If the bug touches a **Tiger invariant** (see fenced section at the end), it is Serious by definition.

---

## Non-negotiable rules (each prevents a specific failure)

1. **Do not edit first.** Show evidence before touching code: a failing test, a reproducible
   command, an exact UI path, a prod log pattern, a webhook replay, queue/job state, or an
   API request/response. *Why: editing before reproducing means you're fixing a guess, and you
   can't prove the guess was right.* If you can't reproduce, stop and report what evidence exists.

2. **State Expected vs Actual.** Every bug is written as `Expected: / Actual: / Scope: / Risk:`.
   *Why: an unstated expectation is an unfalsifiable bug — you can't prove it's fixed.*

3. **Isolate the layer.** Name the *first* point where reality diverges from expectation (UI,
   API route, service fn, DB query, queue/job, webhook, external provider, auth/session, tenant
   boundary, env/config, test fixture). Don't patch multiple layers unless evidence proves the
   bug crosses them. *Why: multi-layer edits hide which change was the fix.*

4. **One hypothesis at a time**, in the form: `Because [cause], [wrong behavior] occurs when [trigger].`
   *Why: changing several things on multiple guesses produces a green test you can't explain.*

5. **Smallest safe patch.** Only the change that fixes the proven cause. **Forbidden mid-debug**
   unless explicitly required: redesigns, opportunistic cleanup, broad refactors, moving files,
   changing public contracts / wizard flow / production behavior outside the bug surface, or
   touching adjacent systems "while here." *Why: every extra changed line is new untested surface.*

6. **Add a regression guard.** Every serious bug leaves behind at least one of: unit/contract/
   integration test, webhook-replay test, tenant-isolation test, UI regression test, smoke test,
   monitor/log assertion, or documented invariant. **Validity check: if the fix is reverted, the
   new guard must fail.** *Why: a guard that passes without the fix doesn't guard anything.*

---

## Procedure (Serious Mode)

### 1. Failure card
```
Bug:
Expected:
Actual:
First observed:
Affected area:
Recent changes:      # git log / git diff since last-known-good
Risk level:
Repro status:
```

### 2. Reproduce — *as a failing automated test when feasible*
Use the smallest reproduction. **Prefer making the repro a red test** (drive it with
`superpowers:test-driven-development`): the repro then becomes the regression guard in step 6,
and "Proof before/after" = the test going red→green. Acceptable proof: command output, failing
test, local UI path (capture via `/browse`), API call, webhook replay, queue inspection, log excerpt.

If reproduction fails, **stop** and report:
```
Could not reproduce yet.
Evidence found:
Evidence missing:
Recommended next probe:
```

### 3. Identify the first broken layer
Ask: *where does reality first diverge from expectation?* For **regressions, use `git bisect`**
(or diff against last-known-good) to find the introducing commit before theorizing — it is
faster and surer than guessing.

### 4. State one hypothesis + log the attempt
```
Attempt N hypothesis: Because [cause], [wrong behavior] occurs when [trigger].
```
Keep a running list of attempts and their results. **After 3 failed hypotheses, stop** (see Stop Conditions) — count from this log, don't loop blindly.

### 5. Patch narrowly
Before editing, list:
```
Likely files to change:
Files intentionally NOT touching:
```

### 6. Add / update the regression guard
The guard must prove the *exact* failure (e.g. "webhook replay creates one job, not two";
"Tenant A cannot read Tenant B lead detail"). Revert-the-fix check must hold (rule 6).

### 7. Run the correct gate
Real `tiger-claw-v4-core` scripts (npm + vitest + tsc). Backend bugs → run from `api/`;
wizard/dashboard bugs → run from `web-onboarding/`.

- **Fast Gate** (small bugs): `api/` → `npm test -- <path/to/file.test.ts>` (vitest)
- **Local Confidence Gate** (normal bugs): targeted test → related suite → `npm run build` (tsc = typecheck)
- **Merge Gate** (before PR):
  - `api/`: `npm run build && npm test && npm run security:static`  *(build runs the `architecture-guard` prebuild automatically)*
  - `web-onboarding/`: `npm run lint && npm run build && npm test`
- **Production-Risk Gate** (Stripe / auth / tenant / queue / messaging / wizard / deploy):
  Merge Gate **plus** the targeted suites covering the touched invariant — tenant isolation
  (`api/src/test-helpers/` + integration tests), Stripe webhook replay/idempotency
  (`api/src/commerce/__tests__/`), security static gates (`npm run security:static`), drift
  guard (`api/src/__tests__/drift_guard.test.ts`). If no dedicated check exists for the
  invariant you touched, that gap is itself a finding — flag it.

> Note: api tests need `TIGER_CLAW_API_URL=http://localhost:4000` — the `npm test` script already sets it.

### 8. Final report (required)
```
Root cause:
Fix:
Files changed:
Regression guard:        # and how it fails if the fix is reverted
Proof before:
Proof after:
Risk:
What was NOT touched:
Follow-up, if any:
```
Then commit as **one atomic commit per fix**, referencing the failure card — use `/ship`.

---

## Devil's Advocate check (before closing)
Run this yourself; for Serious bugs, optionally run `/codex challenge` on the diff.
- What if this only hides the symptom?
- What adjacent behavior could it break?
- Could it cause duplicate sends, duplicate charges, or leaked data?
- Could it fail differently in prod than locally? Could it be env/config, not code?
- Could it be stale test data, a race condition, or a tenant-boundary issue?
- Could the bug return through another path?

If any answer is concerning, add a test, monitor, or follow-up note before closing.

---

## Stop Conditions — stop and ask for human review if:
- 3 hypotheses fail, or reproduction can't be established
- the fix needs a schema migration, deletes data, or changes a public contract
- the fix changes payment, tenant-access, auth/session, or production-deploy behavior
- the bug reveals a broader architectural flaw

Escalation report:
```
What was tested:
What was ruled out:
What evidence remains:
Most likely next investigation:
Recommended human decision:
```

---

<!-- =========================================================================
     TIGER-SPECIFIC — applies ONLY when working in the tiger-claw-v4-core repo.
     Skip this section entirely in any other project.
     ========================================================================= -->
## 🐯 Tiger-Specific (tiger-claw-v4-core only)

**Invariants that must remain true — a bug touching any of these is Serious Mode:**
- A tenant cannot read or mutate another tenant's data.
- A Stripe event can be replayed without duplicate business effects.
- A paid checkout creates the correct customer state exactly once.
- A refund/cancel action records an audit event.
- A follow-up job must have a deterministic id.
- A claimed contact may expose action links only when allowed; an unclaimed contact is
  read-only and must not leak restricted action links.
- A channel-provider failure must not corrupt lead state.
- The onboarding wizard must not advance until required credential checks pass.
- API keys and channel tokens must never be logged.
- Production deploys must not occur without explicit approval.

**Gate commands (verified against the repo 2026-06-13):**
```
# typecheck/build (api):  cd api && npm run build          # tsc; runs architecture-guard prebuild
# all tests (api):        cd api && npm test               # vitest; sets TIGER_CLAW_API_URL=:4000
# single test:            cd api && npm test -- <file.test.ts>
# security static gates:  cd api && npm run security:static
# wizard build/lint/test: cd web-onboarding && npm run build | npm run lint | npm test
# tenant isolation / webhook idempotency: no single script — target the relevant
#   *.test.ts under api/src/**/__tests__ (e.g. commerce/__tests__ for Stripe replay,
#   test-helpers/ for tenant isolation). Flag if none covers the invariant you touched.
# stack: Node/Express API (Cloud Run, port 4000) + Next.js wizard; PostgreSQL + Redis/BullMQ.
```

---

## Skill standard
A debugging run succeeds only when: the failure is understood, the fix is narrow, the proof is
visible, the regression is guarded, the risk is stated, and the lesson is recorded.

**Every serious bug must leave behind a test, monitor, guardrail, or documented invariant.**
