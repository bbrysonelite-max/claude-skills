---
name: the-loop
description: Brent's canonical build-and-debug pipeline — ground-truth audit, spec, plan, independent tests, PR, CI, independent review, HIS merge, live proof, write-down — with hard role separation between builder, reviewer, and test author. Use when Brent says "follow the flow", "the loop", "run the loop", "follow the pipeline", or before ANY non-trivial build, fix, or debug on his projects. Skipping a step is vibe coding; skipping the audit is vibe debugging.
---

# The Loop

Ten gates (0–9). In order. No gate skipped, no gate merged into its neighbor.
The loop's exit feeds its entrance: step 9's write-down is step 0's next audit.

Brent's canonical 8-step statement (dictated 2026-08-24, maps onto the gates):
1 ground-truth read-only audit (dispatched agent) → 2 spec amended only from
audit receipts → 3 plan + independent test-writer, sabotage RED-proven →
4 PR + CI → 5 independent adversarial review, verdicts with own receipts →
6 merge = BRENT'S call, each on his word → 7 prove it after merge (browser
walk, or bounce + live eval for daemons) → 8 loop: the running audit is
step 1 of the next cycle.

## The gates

0. **GROUND-TRUTH AUDIT** — read-only, before anything. DISPATCHED as its own
   read-only audit agent per slice (never the builder, never the orchestrator's
   guess). Read the real thing in the real place NOW: live logs, running
   containers, actual files, live queries. No memory, no docs-as-proof, no
   "right shape" guessing. Absence is a measurement — a zero needs the query
   that produced it. Output: what is actually true, with command + output + UTC.
1. **SPEC** — one file, simple artifact first, AMENDED ONLY FROM AUDIT
   RECEIPTS — never from memory or intention. What changes, what never
   changes, what "working" means (observable behavior, not vibes). Name the
   one thing most likely to make it wrong.
2. **PLAN** — slices, not timelines. Each slice: smallest provable unit,
   its prove-it receipt named in advance, its rollback named in advance
   (SAFE ROAD: backup + TESTED rollback before anything live).
3. **INDEPENDENT TESTS** — written by an agent that did NOT and will NOT
   write the implementation, from the behavior contract only. Persisted in
   the repo's test suite, never ad-hoc shell history. Sabotage check: delete
   or break the code — tests MUST go red. A test that can't fail is a lie.
4. **PR** — branch, never main. Stage by path, never `git add -A`. One
   slice per PR.
5. **CI** — green on the PR, watched to completion. Skipped/gated tests are
   not green — say so.
6. **INDEPENDENT REVIEW** — a different agent than the builder, read-only
   tools, own context, ADVERSARIAL by instruction. Verdicts carry the
   reviewer's OWN receipts (its own commands + output + UTC), never a
   restatement of the builder's. Builder applies findings; reviewer
   re-passes the delta. No agent ever grades its own work.
7. **MERGE = BRENT'S CALL** — present the PR + receipts, one plain yes/no.
   Never merge, never push to main, never "while I was at it."
8. **PROVE IT LIVE** — after merge/deploy, walk the real path with real eyes.
   Two variants by project class, same bar:
   - **UI product (Tiger, sites):** real browser, real click path, live
     endpoint SHA-matched to the merge.
   - **Daemon/service (Jumbo, bridges, runners):** BOUNCE the service
     (bootout/bootstrap — never kickstart where that law applies), then a
     LIVE EVAL against the bounced process, then wire/read its probes.
   Receipt = command + observed output + UTC. Anything not walked is labeled
   UNVERIFIED, out loud.
9. **WRITE IT DOWN** — reconcile living docs, capture durable decisions to
   memory (local + Jumbo), append the session/flight record. What you wrote
   becomes the next loop's ground truth. Not written = will be re-derived
   wrong later.

## Role separation (hard)

| Role | Rule |
|---|---|
| Orchestrator (Fable) | Runs the loop, writes ZERO code |
| Builder (Opus) | Writes code, never tests it, never reviews it |
| Test author | Third agent, blind to implementation, contract only |
| Reviewer | Read-only tools, separate context, re-reviews every fix delta |
| Brent | Merges, decides spend, adjudicates — the only human gate |

## Debugging is the same loop

"Vibe debugging" = fixing before auditing. A bug enters at gate 0: reproduce
it live and read the actual failure (the exact log line, the exit code) before
naming a cause. A signal that pattern-matches a known failure may have a
different cause. Then spec the fix and run the remaining gates. A designed
refusal (a cap, a guard) is not a bug — it is the system asking a human a
question; route it to Brent as one plain decision.

## Standing laws the loop inherits

- Prove-it gate: command + output + UTC, or the word UNVERIFIED.
- Fail loud: every non-healthy state names the missing fact and the action.
- Spend and irreversibles halt for Brent: `DECISION REQUIRED: [what] — [A] vs
  [B] — [recommendation]`. Everything reversible proceeds and reports.
- Flag, don't fix: wrong things outside the slice get one line, not a detour.
- Never trust a subagent's report — diff the disk.
