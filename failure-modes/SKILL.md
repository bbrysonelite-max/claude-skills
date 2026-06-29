---
name: failure-modes
description: A comprehensive, grounded method (FMEA + pre-mortem + red-team) that sweeps every failure surface of a target — software, module, process, or workflow — names every way it can fail from the micro level to the macro level, then INVERTS each failure into the specific designed strength that cancels it. Exhaustive by design; produces concrete security/UI/UX/reliability improvements as output. Distinct from blind-spots-audit (which finds unknown-unknowns) — this is the systematic sweep of mostly-known surfaces. Use when Brent says "failure modes", "how can/would this fail", "how do I fail", "FMEA", "pre-mortem", "fortify/harden this", "stress every surface", "where is this weak", "make it bulletproof", or before shipping / when designing for robustness.
---

# failure-modes

*"Tell me every possible failure point, every margin, every surface — how to fail miserably, micro
and macro. Then do the exact opposite: make each failure point's inverse the strength."*

A grounded **method**, not a brainstorm. It runs on two axes at once:
**micro → macro** (a line of code → the module → the system → the business) and
**failure → fortification** (each mode flips to a specific designed strength).

It is **not** `blind-spots-audit` (that hunts the *unknown* unknowns); this is the exhaustive,
repeatable sweep of the *known* failure surfaces. It is **not** `production-gate-audit` (that builds
a CI/test gate for a repo); this analyzes any target and outputs a fortification spec.

## Workflow

1. **Anchor on the real target** (inherits `ground-truth`). Read the actual code / flow / config /
   process — not the shape, not memory. State the target type (software · module · process ·
   workflow) and exactly what you read. A failure analysis from imagination is fiction.
2. **Sweep ALL 32 surfaces across the 5 bands** in [REFERENCE.md](REFERENCE.md). For each surface,
   name the failure mode(s) it exposes, micro → macro. **Mark a surface `N/A` explicitly with a
   one-word reason** when it truly doesn't apply — coverage is provable; never silently skip.
   **Band E (business/compliance/reputation) is always swept**, weighted by target type.
3. **Invert each failure → the strength.** For every mode, write the specific control/change that
   cancels it AND how you'd detect/verify it. Concrete ("parameterize the query + add a fuzz test"),
   never vague ("be more secure"). This inversion is the product, not the scary list.
4. **Tag each mode** `GROUNDED` (seen in the artifact, cite it) or `GENERAL-RISK` (applies by class,
   not yet confirmed here). No invented modes — if it doesn't fit the real target, cut it.
5. **Deliver structured** (see REFERENCE output template): grouped by band, a row per mode, then a
   short **Top Fortifications** rollup — the highest-leverage strengths to build first. Exhaustive
   in coverage, ruthless about padding.

## Scale to the target

- Small module / single function → one structured pass is enough.
- Large or critical target → **fan out one agent per band** (A–E), each sweeping its surfaces in
  depth; then synthesize and dedupe. Bounded (5 agents), comprehensive.

## Honesty bar

- **Comprehensive ≠ bloated.** Every surface is *considered*; only real modes get a row. `N/A` is a
  valid, honest answer with a reason.
- **Ground or label.** Don't dress a general risk as a confirmed defect.
- **End on strengths.** The deliverable is a fortification plan, not a doom list.

## Quick start

"Run failure-modes on `<file/flow/process>`" → it reads the target, sweeps the 32 surfaces, and
returns the failure→strength map grouped by band + the Top Fortifications to build.
