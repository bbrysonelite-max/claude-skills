# Run Flow & Stopping Rule

## 6. Run flow

1. **Seed.** Operator names a starting point — a vertical, an opportunity, or "find a buyer
   around X." The skill creates the root Node (subject = the golden lead for that vertical).
2. **Root question = what's the golden lead.** Posit the diamond (WHAT/WHY/WHO), oriented to
   work *backwards* from the golden lead toward confirming real buyer demand.
3. **Per question, decide known vs. research.** For each of the six: *do I already have this
   from the operator, or must I go dig?* `known` → use/echo it. `needs-research` → dispatch a
   research agent (web search, public APIs, light scraping) to draft an answer **with evidence
   attached.**
4. **Operator confirms each answer.** The skill shows drafts; operator accepts or corrects.
   This is the hybrid loop — nothing becomes "settled" without a confirmation.
5. **Spawn children.** Any answer that is unproven or high-value becomes a child Node, and the
   six questions run on it. Auto-drills ungrounded branches; operator can force or skip.
6. **Stop at bedrock.** A branch ends when `grounded` (buyer + money-in-hand proof) or at the
   safety depth cap, with operator override.
7. **Hand-off.** Once the buyer is grounded, the skill's final act is to emit the **blueprint**
   (§7) — the golden-lead definition + the ore spec — and **stop.** Finding/producing the lead
   is the Mine's job (stage #2).

## 5. Stopping rule (bounded recursion)

Unbounded recursion is the one thing that can run forever and burn unlimited tokens/time. The
rule:

- A branch is **done** when it is `grounded` — it lands on a verifiable buyer + evidence of
  willingness to pay (money-in-hand).
- Branches without proof keep drilling.
- A **safety depth cap** (configurable) prevents infinite recursion.
- The **operator has the wheel** — can push any branch deeper or call it off early.

Auto-stop at proof, capped for safety, operator override.
