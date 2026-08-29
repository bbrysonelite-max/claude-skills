---
name: tiny-team
description: Runs work as "Tiny but Serious Inc." — one human plus four separated agent roles (Scout researches, Builder builds, Reviewer breaks, Agent Memory preserves), with Brent as the only goal-setter and gate. Use when Brent says "tiny team", "staff this", "run this as a team", "spin up the crew", or when a task is big enough to need parallel roles rather than one agent doing everything.
---

# Tiny Team

```
Tiny but Serious Inc.
├── 👤 Brent  · Sets goals · Makes decisions — the ONLY merge/spend/deploy gate
├── 🔭 Scout  · Research / audit / find — read-only, returns facts with receipts
├── 🛠 Builder · Writes code / builds product — never tests or grades own work
├── 🧪 Reviewer · Tests + breaks — blind test author AND adversarial reviewer
└── 🧠 Agent Memory · Jumbo — preserves what the team learned, supersedes what rotted
```

The org is the separation. A team where one agent scouts, builds, tests, and
grades itself is one agent wearing four hats — that is vibe coding with extra
steps. Roles are separate CONTEXTS (separate subagents), not separate sections
of one agent's answer.

## Role contracts

**👤 Brent** — goals in, decisions out. The team brings him ONE dead-simple ask
at a time with a recommendation. Nothing merges, spends, deploys, or touches a
live system without his word. His "GO" on one slice is not a GO on the next.

**🔭 Scout** — dispatched FIRST, read-only. Ground-truth audit: read the real
thing in the real place (live systems, source, logs, Jumbo knowledge — wiki and
CodeGraph BEFORE walking a repo). Output = facts with file:line + UTC receipts,
options with odds, and the one thing most likely to make the plan wrong. A
Scout that proposes a fix has left its lane — facts only.

**🛠 Builder** — builds from the spec the Scout's audit produced. Reads ground
truth itself (never trusts a summary it can verify), pipe-tests its own work
with receipts, opens the PR. NEVER: writes the tests that gate it, reviews
itself, merges, or touches live config. Judgement calls it makes beyond spec
get FLAGGED in the PR body, not smuggled in silently.

**🧪 Reviewer** — two hats, both blind-at-start: (a) test author who writes the
gating tests FROM THE SPEC ONLY, never having read the implementation — first
contact between blind tests and real code is where the truth comes out; (b)
adversarial reviewer who tries to BREAK the work: probes it live, mutation-tests
the tests (delete a defense — does anything go RED?), and rules on the builder's
flagged judgement calls. Verdicts: APPROVE / APPROVE-WITH-MINORS /
CHANGES-REQUIRED, findings with severity + failure scenario + receipts.

**🧠 Agent Memory (Jumbo)** — not a role you dispatch; a duty every role owes:
- Session start: recall before assuming (auto-inject does this; knowledge API
  for code/doc lookups: CodeGraph + wiki before repo-walking).
- Slice close: write what was PROVEN (receipts, laws learned, debts left) to
  memory + MEMORY.md hook line, same breath as shipping.
- Rot: a fact proven false gets superseded (his GO for strikes), never left
  standing beside its correction.

## Model routing (amended 2026-08-24 — his ruling)

The Agent tool's `model` enum offers only sonnet/opus/haiku/fable; **`opus` resolves to
Opus 4.8**, while the orchestrator runs Fable 5 (above Opus). So route by what a miss costs:

| Role | Model | Why |
|---|---|---|
| 🛠 Builder, blind test author, mechanical edits, log-digging legwork | `model:"opus"` | Volume work, cheapest carrier, keeps Fable off the code |
| 🔭 Scout (audit), 🧪 Reviewer (adversarial break/verdict) | `model:"fable"` or `subagent_type:"fork"` | Judgment roles — a missed BLOCKER costs a day; this is where the tier gap bites |

Token burn is still the governing law ([[fable-orchestrates-opus-codes]]) — this is a
carve-out, not a repeal. Never resume a wrong-model agent; redispatch fresh.

## Dispatch mechanics (learned the hard way, 2026-08-23)

- Scout first, alone. Builder and blind test author may then run in PARALLEL —
  but in SEPARATE WORKTREES; two agents sharing one checkout is a race.
- Every claim any role reports is UNVERIFIED until the orchestrator diffs the
  disk / reruns the command. Never trust a subagent's report.
- Reviewer findings route back: builder fixes code, test author fixes tests,
  each in own lane; spec adjudicates disagreements; spec defects get named as
  spec defects (the builder is not wrong for following a wrong spec).
- Iterate rounds until the Reviewer's verdict is APPROVE-grade, then bring
  Brent the merge ask. Deploy is a SEPARATE ask after merge.
- The build process inside this org chart IS `the-loop` — invoke that skill for
  the nine gates; Tiny Team is who runs them, the-loop is what they run.

## Cost discipline (his ruling 2026-08-24, from evidence)

**The audit is not the expense — it is the insurance.** Read-only Scout runs are
~10% of a campaign's cost and produced most of its value: 2026-08-23/24 they
found recall silently dead on both Macs, an unauthenticated datastore on the
LAN, and a silent model downgrade — three things he was blind to. His words:
*"I wouldn't [be generating revenue] if I were wrong."* Never economize here.

**The expense is polishing code that has no field evidence yet.** The credential
gate took 4 PRs and 3 review rounds; its own log showed one test fire and one
false fire and zero caught incidents. Round 1 found the real BLOCKER; rounds
2–3 found minors and test debt. That is where the money went.

Standing rules, cheapest first:

1. **Scout always, first, alone.** Read-only, no build until its facts land. If
   Scout says stale / as-designed / already-ruled → **STOP.** Do not build to
   look thorough.
2. **One review round by default.** A second round only if round 1 returned a
   BLOCKER or HIGH. Minors get recorded in the deploy doc, not chased.
3. **No polish PR without field evidence.** Wait for the thing to fire in the
   wild and produce a receipt before hardening it further.
4. **Orchestrator may write the tests** when the surface is small or the agent
   API is flaky — legitimate whenever it did not write the implementation and
   has not read its source. Label the authorship honestly (grey-box ≠ blind).
   2026-08-24: two blind-author dispatches died on 529s; the orchestrator wrote
   65 checks in one pass, first-contact green, sabotage-proven. Cheaper and no
   reconciliation round.
5. **Reuse live ground truth as fixtures** — the real transcript, the real 401,
   the real log. Free, and it tests what actually happens.
6. **Model routing by cost, not habit:** Scout on Fable (judgment pays there);
   Builder and test authors on `opus`; Reviewer on `opus` by default, Fable only
   for a BLOCKER-class judgment call.

## Sizing

Size by **blast radius**, not by ambition:

| Work | Staffing |
|---|---|
| Read-only question, docs, audit | 🔭 Scout only |
| One file, nothing live, reversible | 🛠 Builder + orchestrator disk-verify |
| Gates every turn/prompt, or touches a live system, or unknown root cause | Full org (Scout → Builder ∥ tests → Reviewer) |

When unsure, staff it — the 08-23 campaign caught a silent-blackout BLOCKER and
three false-green tests ONLY because the roles were separate people. But
"unsure" means unsure about the RISK, never about wanting to look thorough.
