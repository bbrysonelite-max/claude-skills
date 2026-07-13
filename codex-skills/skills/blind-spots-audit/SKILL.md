---
name: "blind-spots-audit"
description: "Surface what Brent ISN'T asking, the assumptions in play, what the work missed, and what the agent itself got wrong \u2014 the inverse of grill-me (grill-me stress-tests a plan you have; this surfaces what you don't have). Produces a grounded, prioritized list of blind spots, each with the specific question to ask or thing to verify, ending with the top few to resolve before proceeding. Use when Brent says \"what am I not asking\", \"what don't I know\", \"what should I ask\", \"what did I forget\", \"what did we miss\", \"what did you miss\", \"blind spots\", \"devil's advocate\", \"poke holes\", or at the end of a build / before a consequential decision."
---

# blind-spots-audit

Find the questions that weren't asked and the gaps no one named. Brent's own words for it:
*"What do I need to ask? What did I forget to ask, and what did you forget?"*

This is the **opposite of grill-me**: grill-me interrogates a plan Brent *brings*; this enumerates
what Brent (and the agent) didn't think to raise. It inherits **ground-truth** — base every blind
spot on the actual artifact/state, not generic platitudes, and label each grounded vs. hypothesis.

## Workflow

1. **Anchor on the real context.** Read the actual thing — the plan, the diff, the "done" work,
   the decision, the current state. Don't audit from memory or the shape. If you haven't seen it,
   look first. State what you anchored on.
2. **Sweep the seven lenses** (see [REFERENCE.md](REFERENCE.md) for the probing question per lens):
   - **Unasked questions** — decisions being made implicitly that should be explicit.
   - **Assumptions** — what's taken for granted, by Brent AND by you; mark each verified / UNVERIFIED.
   - **Missed coverage** — what the work/plan didn't touch (edge cases, the unhappy path, verification skipped).
   - **Failure modes** — what breaks; second-order effects, cost, consent, drift, security.
   - **Affected parties** — customer, operator, future-Brent, the business — who wasn't considered.
   - **Devil's advocate** — the strongest case AGAINST the current direction.
   - **Unknown-unknowns probe** — what whole category hasn't been looked at (a modality not run, a source not read, a stage not grounded)?
3. **Self-audit — what did I, the agent, miss or get wrong?** Call out your own skipped steps,
   ungrounded claims, and assumptions. For consequential calls, spawn an INDEPENDENT agent to do
   this pass (the same eyes that made an assumption rarely catch it — ground-truth §10).
4. **Ground or flag.** For each blind spot, either verify it now (and cite) or label it a
   hypothesis to check. Drop the ones that don't survive contact with the real context — no padding.
5. **Prioritize and deliver.** Rank by stakes × likelihood. Output the list, then the **top 1–3 to
   resolve before proceeding**, each as a concrete question to answer or thing to verify. One
   recommendation per item, not a menu.

## Scale to stakes

- Quick decision / small change → a single inline sweep is enough.
- High-stakes (customer-facing, irreversible, "done" being declared, a locked decision) → escalate:
  dispatch independent agents per lens (or N skeptics each told to find the fatal flaw), then
  synthesize. Don't self-defend a consequential call.

## Honesty bar (non-negotiable)

- **No invented blind spots.** A blind spot you can't tie to the real context is noise — cut it.
- **Surface, don't soothe.** The job is to find what's wrong/missing, not to reassure. If the work
  is genuinely solid, say so plainly and show the few real residual risks.
- **Name what it'd take to close each gap** — the question to ask, the command to run, the person to confirm with.

## Quick start

Point it at a target: "blind-spot this plan" / "what am I not asking about X" / "what did we miss
on the skills work." It reads the target, runs the sweep, and returns the prioritized list + top-3-to-resolve.
