---
name: production-debugging-loop
description: >-
  Use when debugging any failure, regression, broken test, or production incident —
  including payment/Stripe bugs, webhook or queue/job failures, auth/session issues,
  tenant-isolation leaks, onboarding/wizard failures, UI regressions, or agent
  behavior bugs. Especially for the Tiger / tiger-claw-v4-core codebase, where it adds
  money/tenant/webhook invariants. For a build, or for a debug run inside Brent's full
  pipeline (audit → spec → plan → independent tests → PR → review → HIS merge → prove),
  use /the-loop instead — that is the pipeline, this is the procedure it runs at the bug.
---

# Production Debugging Loop

Debugging is a closed loop. Not done when the symptom disappears — done when there is
evidence the bug was understood, fixed, and guarded against returning.

```
Failure → Reproduce → Isolate → Hypothesize → Patch → Prove → Prevent → Record
```

Never waived: **no patch without evidence · no completion without proof · no serious bug
closes without a regression guard.**

**Receipts:** command + output + UTC, or the word UNVERIFIED. "Proof before / Proof after"
is the actual output, red→green — never a remembered result, never a ✅.

Defers to `superpowers:test-driven-development` (the failing test),
`superpowers:verification-before-completion` (before any "fixed" claim), `/investigate`
(root cause), `/browse` or `/qa` (UI proof), `/codex challenge` (adversarial), `/ship`
(the commit).

## Mode — when in doubt, Serious

- **Small:** typos, labels, local styling, a broken import, a harmless fixture →
  Reproduce → Patch → targeted test → report files + proof.
- **Serious:** money, Stripe, refunds, auth, API keys, tenant isolation, messaging delivery,
  lead ownership, queue jobs, webhooks, onboarding, production data, permissions, deploys —
  or any bug where a wrong fix could leak data, duplicate work, lose money, or break trust.
  A bug touching a **Tiger invariant** is Serious by definition.

## Rules (each prevents a specific failure)

1. **Evidence before code** — a failing test, a reproducible command, an exact UI path, a
   prod log pattern, a webhook replay, queue/job state, or an API request/response. Editing
   before reproducing is fixing a guess. Can't reproduce → stop, report what evidence exists.
2. **Expected vs Actual** — `Expected: / Actual: / Scope: / Risk:`. An unstated expectation
   is an unfalsifiable bug.
3. **Isolate the layer** — name the *first* point where reality diverges (UI, API route,
   service fn, DB query, queue/job, webhook, external provider, auth/session, tenant
   boundary, env/config, test fixture). Multi-layer edits hide which change was the fix.
4. **One hypothesis at a time:** `Because [cause], [wrong behavior] occurs when [trigger].`
   Several guesses at once produce a green test you can't explain.
5. **Smallest safe patch.** Forbidden mid-debug unless explicitly required: redesigns,
   opportunistic cleanup, broad refactors, moving files, changing public contracts / wizard
   flow / production behavior outside the bug surface, touching adjacent systems "while
   here." Every extra changed line is new untested surface.
6. **Regression guard** — unit/contract/integration test, webhook-replay, tenant-isolation,
   UI regression, smoke test, monitor/log assertion, or documented invariant. **Revert the
   fix and the guard MUST fail.** A guard that passes without the fix guards nothing.

## Procedure (Serious)

1. **Failure card:** `Bug / Expected / Actual / First observed / Affected area / Recent
   changes (git log since last-known-good) / Risk / Repro status`.
2. **Reproduce as a failing test** where feasible — the repro then *is* the guard, and
   before/after is red→green. Proof may also be command output, a `/browse` UI path, an API
   call, a webhook replay, queue inspection, a log excerpt. Can't reproduce → **stop**:
   `Evidence found / Evidence missing / Recommended next probe`.
3. **First broken layer.** For regressions, `git bisect` (or diff last-known-good) before
   theorizing — faster and surer than guessing.
4. **One hypothesis, logged.** Keep the running attempt list. **After 3 failures, stop** —
   count from the log, don't loop blindly.
5. **Patch narrowly.** First list `Likely files to change` and `Files intentionally NOT touching`.
6. **Guard the exact failure** ("webhook replay creates one job, not two"; "Tenant A cannot
   read Tenant B lead detail"). The revert check of rule 6 must hold.
7. **Run the gate** (commands below). Backend from `api/`, wizard/dashboard from `web-onboarding/`.
   - **Fast** (small): the targeted test. **Local Confidence** (normal): targeted test →
     related suite → `npm run build` (tsc). **Merge** (pre-PR): `api/` build + test +
     `security:static`; `web-onboarding/` lint + build + test.
   - **Production-Risk** (Stripe / auth / tenant / queue / messaging / wizard / deploy):
     Merge Gate **plus** the suites covering the touched invariant — tenant isolation
     (`api/src/test-helpers/` + integration tests), Stripe replay/idempotency
     (`api/src/commerce/__tests__/`), `npm run security:static`, drift guard
     (`api/src/__tests__/drift_guard.test.ts`). No dedicated check for the invariant you
     touched? That gap is itself a finding — flag it.
8. **Final report:** `Root cause / Fix / Files changed / Regression guard (+ how it fails if
   reverted) / Proof before / Proof after / Risk / What was NOT touched / Follow-up`. Then
   one atomic commit per fix, referencing the failure card — use `/ship`.

## Before closing

Devil's advocate: only hiding the symptom? adjacent breakage? duplicate sends, duplicate
charges, leaked data? fails differently in prod — env/config rather than code? stale test
data, a race, a tenant boundary? returns through another path? Anything concerning → add a
test, monitor, or follow-up note first. Serious bugs: optionally `/codex challenge` the diff.

**Stop and ask for human review if** 3 hypotheses fail or repro can't be established · the
fix needs a schema migration, deletes data, or changes a public contract · it changes
payment, tenant-access, auth/session, or production-deploy behavior · the bug reveals a
broader architectural flaw. Escalate as `What was tested / What was ruled out / What
evidence remains / Most likely next investigation / Recommended human decision`.

---

<!-- TIGER-SPECIFIC — tiger-claw-v4-core ONLY. Skip entirely in any other project. -->
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

**Every serious bug leaves behind a test, monitor, guardrail, or documented invariant.**
