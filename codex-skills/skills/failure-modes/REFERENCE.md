# failure-modes — reference

## The surface taxonomy (32 surfaces, 5 bands) — the spine

Sweep every surface. For each: name the failure mode(s) micro→macro, or mark `N/A (reason)`.
Then invert each mode to the strength that cancels it.

### Band A — Core mechanics (does it do the right thing?)
1. **Correctness / logic** — wrong output, bad math, inverted conditionals, mis-implemented spec.
2. **Edge & boundary** — empty/null/zero/negative/one/max/huge; off-by-one, fence-posts, limits.
3. **State & lifecycle** — invalid transitions, stuck/orphaned state, resurrection, partial completion.
4. **Idempotency & retries** — double-submit, replays, retries that duplicate or corrupt.
5. **Time** — timezone/DST/leap, clock skew, ordering by timestamp, expiry windows.
6. **Numeric & encoding** — precision/rounding/float, overflow, unicode/emoji, locale formats.
7. **Concurrency** — races, lost updates, deadlock/livelock, lock contention, distributed ordering.

### Band B — Data & security (can it be corrupted or attacked?)
8. **Data integrity** — corruption, partial writes, consistency, validation gaps, schema/migration drift, stale cache.
9. **Durability & privacy** — loss, no backup/recovery, PII handling, retention/redaction, unbounded growth.
10. **Tenant / scope isolation** — cross-tenant leak, authz scoping, "what happens to one happens to all."
11. **AuthN / AuthZ** — weak/missing auth, spoofing, privilege escalation, IDOR, missing checks.
12. **Injection & input trust** — SQL/command/XSS/prompt-injection, deserialization, SSRF/CSRF, unsanitized input.
13. **Secrets & supply chain** — keys in code/logs/commits, TLS/MITM, dependency/typosquat, token expiry.
14. **Abuse & DoS** — rate-limit gaps, resource-exhaustion attacks, fraud, replay, repudiation (no audit). *(11–14 ≈ STRIDE.)*

### Band C — Resilience & operations (does it hold up, and can you see it?)
15. **Reliability / availability** — single points of failure, crash-recovery, graceful degradation vs hard fail, DR (RTO/RPO).
16. **Failure handling itself (meta)** — swallowed errors, fallbacks that mask, retries that hide root cause, `{ok:true}` that didn't work.
17. **Timeouts & cascades** — hangs, deadlocks, retry storms, missing circuit-breakers/backpressure.
18. **Performance & scale** — latency/throughput under load, N+1/unbounded queries, hot spots, cold start.
19. **Resource & cost** — memory/CPU/disk/connections/handles exhaustion, and the bill at scale.
20. **Integration & dependencies** — API contract/version breakage, partner changes, network partition, webhook delivery/order/dedupe, failover correctness.
21. **Deploy & config** — deploy/rollback failure, config/env drift, migration ordering, kill-switches/flags, secret rotation.
22. **Observability** — silent failures (no logs), no metrics, no tracing, no alerting, audit-trail gaps.

### Band D — Human-facing (can a real person use it without falling off a cliff?)
23. **UI / visual** — layout/responsive breakage, contrast/accessibility (a11y, color-blind, screen reader), text overflow, i18n/RTL, device/browser compat.
24. **State coverage** — missing loading/empty/error/success states; dead ends with no recovery path.
25. **UX / flow** — confusing copy & jargon, too many steps, no feedback, unclear next action, WIIFM unclear, onboarding cliff, unhelpful errors.
26. **Operator / human** — footguns, insufficient guardrails, alert fatigue, work-burden, automation complacency, handoff drops, docs/training gaps.
27. **Trust & dark patterns** — eroded trust; inverse-to-avoid: pre-checked upsells, hidden pricing, confirmation mazes.

### Band E — Business, process & change (does it survive the real world and time?) — ALWAYS swept
28. **Money & commerce** — billing errors, revenue leak, payment/refund failures, fraud cost.
29. **Legal & compliance** — consent ("stop means stop"), privacy law, A2P/10DLC/TCPA, SLA/contract breach.
30. **Reputation** — public-trust failure, the screenshot that spreads, the overclaim that gets caught.
31. **Process / workflow** (non-software targets) — bottlenecks, single-owner/bus-factor, unclear ownership, manual steps that don't scale, no verification gate, approval logjams.
32. **Drift & maintenance** — doc-vs-reality drift, tech-debt accumulation, deprecation, knowledge loss, rot of unused parts.

## Target-type weighting
- **Software / module** → Bands A–C heaviest; D if it has an interface; E always (cost, compliance, drift).
- **Process / workflow** → Bands D–E heaviest, esp. #31; A–C reinterpreted (a "race" = two people doing the same step, a "timeout" = a handoff that stalls).
- Never drop a band silently — mark its surfaces `N/A (reason)`.

## Output template

```
Target: <what> (<type>) — anchored on: <files/flow you actually read>

BAND A — Core mechanics
| Surface | Failure mode (micro→macro) | Sev×Likelihood | Detection | → Strength (the fix + how to verify) | tag |
| 1 Correctness | ... | High×Med | ... | ... | GROUNDED |
| 5 Time | N/A (no time logic) | — | — | — | — |
...(Bands B–E)...

TOP FORTIFICATIONS (highest-leverage strengths to build first)
1. <strength> — kills <modes> — effort <S/M/L>
2. ...
```

## Fan-out escalation (large / critical targets)
Dispatch one agent per band (A–E), each told: *"sweep your band's surfaces against this target
exhaustively; name every failure mode micro→macro and its inverted strength; mark N/A with a reason;
ground each in the artifact."* Synthesize, dedupe across bands, build the Top Fortifications rollup.

## Distinctions (so it doesn't collide)
- **blind-spots-audit** = unknown-unknowns, prioritized top-3, "what am I not seeing." This = known surfaces, exhaustive, "how does it fail everywhere + how to fortify."
- **grill-me** = interrogate a plan you bring. **production-gate-audit** = build a CI/test gate for a repo. **ground-truth** = verify what's true (this skill's anchor step is an instance of it).
