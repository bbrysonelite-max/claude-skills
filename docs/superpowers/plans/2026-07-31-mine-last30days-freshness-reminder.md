# Mine Last30Days Freshness Reminder Plan

## Goal

Add the every-run Last30Days freshness reminder to the canonical Mine skill and deterministically propagate it to the generated Codex skill without changing Mine execution behavior.

## Roles

- Root agent: ground truth, specification, plan, PR ownership, CI orchestration, and evidence ledger.
- Independent test author: pressure scenario and RED tests only.
- Separate implementer: canonical skill edit and deterministic regeneration only.
- Independent specification reviewer: requirement coverage verdict after CI.
- Independent quality reviewer: final quality verdict after specification compliance.
- Brent: sole merge authority.

## Sequence

1. Record the clean baseline and preserve unrelated changes in the main checkout.
2. Commit this specification and plan on `feat/mine-last30days-reminder`.
3. Give an independent test author the spec. Require a pressure scenario that invokes Mine under time pressure with an already-selected vertical and a Last30Days installation of unknown freshness.
4. Require the test author to add focused tests that fail because both canonical and generated Mine skills omit the reminder. The test commit must not change either skill file or builder code.
5. Give a separate implementer the spec, RED evidence, and test commit. The implementer edits `mine/SKILL.md`, runs the deterministic builder, and commits only the intended canonical/generated artifacts.
6. Root independently runs the focused test, builder check, full 341-test baseline plus the new tests, diff checks, and generated-source integrity checks.
7. Push the branch and open a draft PR. Wait for all available GitHub checks.
8. Obtain an independent `SPEC_COMPLIANT` verdict, then an independent quality `APPROVED` verdict on the same pushed SHA. Route findings back through the independent test author and separate implementer if needed.
9. Leave the PR unmerged and report what remains undone, unproven, and unverified.

## Verification commands

From the repository root:

```bash
python3 codex-skills/scripts/build.py --check
git diff --check origin/main...HEAD
```

From `codex-skills/`:

```bash
python3 -m unittest tests.test_mine_skill
python3 -m unittest discover -s tests
```

## Guardrails

- Do not edit or merge `main`.
- Do not alter Brent's existing `.gitignore` change in the main checkout.
- Do not edit the generated Mine skill by hand.
- Do not fetch, print, copy, or validate credential values.
- Do not update the Last30Days dependency as part of this PR.
- Do not run live research or lead generation for this documentation change.
