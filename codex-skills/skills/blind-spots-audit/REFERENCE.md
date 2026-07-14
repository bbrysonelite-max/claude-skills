# blind-spots-audit — reference

## The seven lenses (the probing question for each)

Run all seven against the **actual** context. Most will surface nothing on a small change — that's
fine; keep only what's real. For each hit, capture: the blind spot · why it matters · the question
to ask or thing to verify · grounded vs hypothesis.

1. **Unasked questions.** "What decision is being made here without anyone deciding it on purpose?"
   Implicit scope, defaults accepted silently, a "since we're here" that wasn't actually chosen.
2. **Assumptions (Brent's AND yours).** "What are we both treating as true that nobody checked?"
   List them. Tag each GROUNDED (cite) or UNVERIFIED (what it'd take). The dangerous ones are the
   assumptions so obvious no one says them out loud.
3. **Missed coverage.** "What did the work/plan NOT touch?" The unhappy path, the empty/zero case,
   the concurrent case, the migration/rollback, the thing that was tested-as-shape but not run.
4. **Failure modes & second-order effects.** "If this is wrong, how does it fail — and what does it
   take down with it?" Cost, consent ("stop means stop"), tenant isolation, drift, security, a
   silent failure that returns `{ok:true}`. What's the blast radius?
5. **Affected parties.** "Who/what is downstream that we didn't picture?" The paying operator, the
   prospect, future-Brent reading this in a month, the business's trust, the next agent.
6. **Devil's advocate.** "What's the strongest argument that this whole direction is wrong?" Steelman
   the opposite. If you can't, that itself is a blind spot (you haven't found the real tradeoff).
7. **Unknown-unknowns probe.** "What entire category have we not even looked at?" A data source not
   read, a modality not run, a stage not grounded, an expert/precedent not consulted. Name the
   category, then name the cheapest probe to illuminate it.

## Self-audit (the agent's own blind spots)

Always include, and be specific — generic humility is useless:
- Which claims did I make from shape/memory rather than direct observation?
- What did I skip to move faster (a verification, an edge case, a re-read)?
- What did I assume about Brent's intent that I never confirmed?
- Where did I say "done" when I only verified the trigger, not the outcome?

For consequential work, this pass is done by an **independent** agent given only the artifact and
the claim — not by the agent that did the work. Self-grounding defends its own assumptions.

## High-stakes escalation (independent panel)

When the call is customer-facing / irreversible / being declared "done" / a locked decision:
- Dispatch independent agents — either one per lens, or N skeptics each instructed: *"find the one
  flaw that makes this fail; default to assuming there is one."*
- Each returns its strongest finding with evidence. Synthesize, dedupe, and keep findings that
  survive (≥ majority or any well-grounded fatal flaw).
- This is the three-agent rule applied to thinking: diverse, independent eyes catch what one can't.

## Output shape

```
Anchored on: <what you actually read/ran>

BLIND SPOTS (prioritized)
1. [GROUNDED] <spot> — why it matters — ASK/VERIFY: <the concrete question or command>
2. [HYPOTHESIS] <spot> — why it might matter — CHECK: <how to confirm>
...
What I (the agent) missed: <specific, honest>

→ Resolve before proceeding (top 1–3): <the few that actually gate the decision>
```

Drop anything that doesn't earn its line. A short, real list beats a long, padded one.
