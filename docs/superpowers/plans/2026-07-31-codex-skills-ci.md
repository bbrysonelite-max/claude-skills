# Codex Skills CI Plan

## Goal

Create the repository's first least-privilege GitHub Actions gate so the Mine reminder pull request is tested by hosted CI rather than relying only on local evidence.

## Roles

- Root agent: read-only ground truth, specification, plan, PR ownership, and evidence ledger.
- Independent test author: RED workflow-contract test only.
- Separate implementer: `.github/workflows/ci.yml` only.
- Independent specification reviewer: workflow and reminder requirement coverage after hosted CI.
- Independent quality reviewer: security and maintainability review after specification compliance.
- Brent: sole merge and later branch-protection authority.

## Sequence

1. Commit this CI specification and plan after the independently tested Mine reminder commits.
2. Have an independent test author add `codex-skills/tests/test_ci_workflow.py` using only the Python standard library. The test must fail because the workflow is absent and must reject privileged triggers, write permissions, secrets, package/network setup, unpinned actions, wrong interpreter coverage, wrong working directory, or missing deterministic commands.
3. Give the RED commit to a separate implementer. The implementer adds only `.github/workflows/ci.yml` and does not edit the test or application/skill files.
4. Root independently runs the focused CI test, builder check, structural validation check, full test suite, YAML-oriented sanity checks, and diff checks.
5. Push the combined branch and open a draft PR. Confirm GitHub recognizes the workflow and wait for both Python matrix jobs plus any external security check.
6. If CI fails, route test changes to the independent test author only when the contract is wrong; route workflow fixes to the implementer when implementation is wrong. Push and rerun all gates.
7. Obtain independent `SPEC_COMPLIANT`, then independent quality `APPROVED`, on the exact final pushed SHA.
8. Leave the PR unmerged. After Brent merges and the check name exists on `main`, separately consider branch protection.

## Verification commands

From `codex-skills/`:

```bash
python3 -m unittest tests.test_ci_workflow
python3 -m unittest tests.test_mine_skill
python3 scripts/build.py --check
python3 scripts/validate.py --check
python3 -m unittest discover -s tests
```

From the repository root:

```bash
git diff --check origin/main...HEAD
```

## Guardrails

- No edit or merge on `main`.
- No credential, secret, cache, package-install, or live-provider step.
- No repository write permission and no persisted checkout credentials.
- No branch-protection mutation in this change.
- No weakening the Mine reminder or generated-skill integrity gates.
