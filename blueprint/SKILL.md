---
name: blueprint
description: Use when defining the golden lead and money-in-hand buyer for a vertical BEFORE any scraping or enrichment is built — stage #1 of The Refinery. Runs a demand-first, recursive who/what/when/where/why/how inquiry (research + operator confirmation) and emits a Golden Lead Definition grounded in a confirmed paying buyer, plus an audit-trail inquiry tree. Trigger on "define the golden lead", "who would pay for this lead", "blueprint a lead for <industry>".
---

# Blueprint — Golden Lead Definition

Stage #1 of The Refinery waterfall. You define **what the golden lead is** and **who pays for
it**, working **demand-first**: find the buyer with money in hand, then reverse-engineer the
lead. A lead "worth $900" is fantasy until a named buyer has $900 in hand. You do **not** scrape
or enrich — you emit the blueprint that the Mine (stage #2) and the refining stage (stage #3)
build toward.

## Before you start

1. Read `references/inquiry-node-model.md`, `references/run-flow.md`,
   `references/research-execution.md`, and `references/tree-schema.md`.
2. Load `config.yaml` (the levers). Honor `confirm_mode`, `depth_cap`, `confidence_threshold`,
   `research_sources`, and `output_root`.
3. Load the schema at `schema_template` (default `templates/golden-record-schema.md`).

## Operating procedure

1. **Seed.** Ask the operator for ONE seed: a vertical, an opportunity, or "find a buyer around
   X". Create the root Node (subject = *the golden lead for that vertical*) and write the initial
   `trees/<industry>-<date>.json` under `output_root`.
2. **Posit the diamond.** State the WHAT/WHY/WHO triad for the golden lead (the perfect-lead
   definition from the model doc), oriented to work backwards from the lead toward a confirmed,
   paying buyer.
3. **Per question, known vs research.** For each of who/what/when/where/why/how: if the operator
   already gave it, mark `known` and echo it; else mark `needs-research` and dispatch a research
   subagent (web search / public APIs / light scraping per `research_sources`) that returns a
   **draft answer with evidence attached** (source + link/quote/number).
4. **Operator confirms (one at a time).** In `confirm` mode, present each drafted answer singly
   and wait for accept/correct before it settles. Never mark `grounded` without evidence. Persist
   the tree after each `grounded` answer.
5. **Spawn children.** Any unproven or high-value answer becomes a child Node; run the six
   questions on it. Auto-drill ungrounded branches; the operator can force deeper or skip.
6. **Stop at bedrock.** A branch ends when `grounded` (the buyer branch requires **money-in-hand**
   evidence) or at `depth_cap`. The operator can override either way.
7. **Hand off.** Once the buyer is grounded, emit BOTH artifacts (below) and STOP. Producing the
   lead is the Mine's job.

## Accessibility

The operator has one eye. Ask **exactly one question per message**, keep replies short and plain,
and minimize scrolling. Never batch questions.

## Output artifacts (write both under `output_root`, then stop)

**`definitions/<industry>-<date>.md`** — the Golden Lead Definition, two halves:
- **A. Diamond spec** — the filled Golden Record Schema (from `schema_template`).
- **B. Ore spec** — what raw source-material has the *latent properties* to become this diamond,
  and therefore where the Mine should dig. (Corollary: you can't refine iron into diamond —
  specify the right raw material, not just the finished shape.)
- Plus: WHY (pain/value), WHO (lead identity + buyer identity), WHEN/WHERE/HOW (the Mine
  hand-off), **Buyer-proof** (named buyer + money-in-hand evidence), **Match statement** (this
  buyer ↔ this product in one sentence), **Verdict** (go/no-go + confidence).

**`trees/<industry>-<date>.json`** — the audit tree per `references/tree-schema.md`. Resumable.

## Done means

A Golden Lead Definition whose verdict is grounded in a **named buyer with evidence of
money-in-hand** — or an honest **no-go** — plus a filled Golden Record Schema, an ore spec, and a
persisted inquiry tree. Then stop.
