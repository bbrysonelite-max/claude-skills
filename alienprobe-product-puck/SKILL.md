---
name: alienprobe-product-puck
description: "Run Alien Probe's evidence-backed product-discovery and 90-day planning discipline. Use for Alien Probe product strategy, deciding the next paid agent-to-agent data SKU, reviewing what agents buy or will pay for, checking whether NAICS/LEI have independent or repeat buyers, evaluating VIN/ICD-10/OSHA/USC/CFR/who/same/alive/changed candidates, answering where the agent-commerce puck is going, or as the Alien Probe planning item inside Daily Checks. Planning and read-only measurement only: never build, deploy, settle, purchase, list, contact buyers, or modify credentials unless Brent separately authorizes that action."
---

# Alien Probe Product Puck

Maintain one honest answer to: **What tiny piece of truth will an autonomous agent pay for next?**

This skill is a product-planning instrument, not an implementation plan. Keep the payment rail and the product hypothesis separate.

## Laws

1. Ground current state from the live service and current repository bytes. Treat Jumbo and prior reports as leads, never proof.
2. Separate transaction readiness from buyer proof. A working `402`, a self-settlement, a known wallet, or an index entry is not independent revenue.
3. Separate gross x402 volume from authentic agent-to-agent commerce. Never repeat a trillion-dollar forecast as today's market size.
4. Prefer one deterministic fact per purchase. Do not recommend seats, dashboards, lead files, dossiers, or subscriptions without completed-buy evidence.
5. Never charge for a malformed subject or a miss. Require strict JSON, stable identifiers, source provenance, freshness, bounded coverage, machine-readable errors, and an agent-controlled spend cap.
6. Never add a SKU because it is easy to build. Admit it only through the product gate below.
7. In Daily Checks mode, make no writes and initiate no payment. Report only.

## Source order

Use the first available source in this order and label anything lower as unverified until reconciled:

1. Live read-only probes of `https://lookups.alienprobe.ai`.
2. Current bytes and settlement evidence in `/Users/brentbryson/company-change-signal/.worktrees/persistent-x402-seller`.
3. Current Alien Probe handoff and research under `/Users/brentbryson/Documents/Last30Days/`.
4. Jumbo memory search for forgotten decisions or leads.
5. Fresh external research only when Brent requests a new market cut or the existing evidence has expired.

Do not rerun `last30days` as a routine daily check.

## Daily mode

Run this compact, read-only pass when invoked by Daily Checks.

### 1. Ground the shelf

- Fetch `/openapi.json` without credentials or payment headers.
- Probe the committed NAICS and LEI exemplar routes without a payment header.
- Record the HTTP status and advertised amount for each route.
- Fetch `/health`; distinguish lookup health from the back-catalog Company Change Signal inventory shelf.
- If the live service cannot be reached, report `UNVERIFIED`; never substitute local code for production.

### 2. Ground buyer proof

Read the newest available settlement/demand evidence and classify every payer as:

- owner or self;
- known tester;
- independent first-time buyer; or
- independent repeat buyer.

Report independent settled revenue separately. If payer ownership cannot be proven, say `unclassified`; do not count it as buyer proof.

### 3. Detect a meaningful change

Check only for deltas since the last evidence cut:

- a new independent payer;
- a repeat purchase;
- a material number of unpaid challenges with no completion;
- a high free-miss rate;
- a source-freshness, rights, coverage, or margin problem; or
- new external payer evidence for a candidate product.

No delta means `HOLD`, not permission to invent another SKU.

### 4. Apply the decision

- `ADVANCE`: at least one independent repeat buyer exists and the proposed next SKU passes the product gate.
- `HOLD`: the machine is healthy but no new demand evidence justifies shelf expansion.
- `INVESTIGATE`: evidence is missing, contradictory, stale, or the live shelf is not behaving as advertised.

### 5. Report five lines

```text
alien_probe_plan  HOLD | ADVANCE | INVESTIGATE
shelf             <live products, prices, and probe result>
buyer_proof       <independent buyers, repeat buyers, verified revenue, or UNVERIFIED>
new_signal        <one meaningful delta or "none">
planning_action   <one bounded research/planning action; never a build action>
```

## Full product-planning mode

Read [references/planning-contract.md](references/planning-contract.md) completely. Re-ground any dated baseline before using it.

For every candidate, produce:

- exact buyer question;
- one-call input and output;
- current demand evidence and its source;
- buyer type and economic principal;
- proposed price and maximum spend behavior;
- source, rights, coverage, freshness, and refresh cost;
- free refusal conditions;
- expected gross margin;
- evidence still missing; and
- verdict: `ADMIT`, `TEST ON PAPER`, `PARK`, or `REJECT`.

## Product gate

A candidate may be recommended for later implementation only when all are explicit:

1. Completed-buy evidence from agents or a clearly labeled experimental thesis.
2. One bounded question and one deterministic answer.
3. Lawful, attributable, freshness-bounded source material.
4. A free malformed/miss path before payment.
5. Gross margin at the proposed per-call price.
6. A reason the answer is needed mid-workflow rather than in a human dashboard.
7. A measurable kill criterion.

When evidence ranks candidates, let the evidence win. The 2026-08-18 baseline ranked VIN ahead of `who`; `who`, `same`, `alive`, `authorized`, and `changed` remain strategic hypotheses until buying behavior proves them.

## Safety boundary

- Do not send payment proofs or authorization headers during planning probes.
- Do not settle a heartbeat transaction to manufacture activity.
- Do not edit or display credentials.
- Do not modify the seller, catalog, pricing, domain, discovery registration, or deployment.
- Do not contact a buyer.
- Stop and request separate authorization if the next step changes external state.

## Dependencies

Required for a grounded daily verdict:

- read access to the persistent seller repository;
- read-only network access to the Alien Probe lookup surface; and
- current non-secret demand or settlement evidence.

If any dependency is unavailable, report `INVESTIGATE` and name the missing evidence. Never silently downgrade to memory.
