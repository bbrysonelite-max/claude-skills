# Codex Skills CI Specification

## Problem

The `bbrysonelite-max/claude-skills` repository has no GitHub Actions workflow, no Actions run history, no ruleset, and no protection on `main`. A pull request therefore cannot satisfy Brent's required "CI does the work" gate.

This harness repair is included before the Mine reminder branch is pushed so that the branch's first pull request can execute its own deterministic checks on GitHub.

## Required behavior

1. Add one workflow at `.github/workflows/ci.yml` named `CI`.
2. Run on pull requests targeting `main` and pushes to `main`. Do not use `pull_request_target`, `workflow_run`, or any privileged trigger.
3. Grant only `contents: read` permission.
4. Cancel superseded runs for the same workflow and pull request/ref.
5. Use `ubuntu-24.04`, a 15-minute job timeout, `PYTHONDONTWRITEBYTECODE=1`, and a matrix containing exactly Python `3.11.15` and `3.14.5`.
6. Default all commands to the `codex-skills` working directory.
7. Run all three deterministic, credential-free gates:
   - `python -m unittest discover -s tests -v`
   - `python scripts/build.py --check`
   - `python scripts/validate.py --check`
8. Pin `actions/checkout` and `actions/setup-python` to verified full commit SHAs. Disable persisted checkout credentials.
9. Do not install packages, invoke `uv`, use caches, access secrets, mutate repository contents, probe providers, or run live skills.
10. Keep `fail-fast: false` so both supported Python versions report evidence.

## Pinned actions

- `actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1` (`v7.0.1`)
- `actions/setup-python@5fda3b95a4ea91299a34e894583c3862153e4b97` (`v7.0.0`)

The read-only audit verified both commits through GitHub and verified that Ubuntu 24.04 x64 artifacts exist for both exact Python versions.

## Acceptance proof

- An independent test author commits a failing standard-library test before the workflow exists.
- A separate implementer adds only the workflow file.
- The focused workflow test and the full repository suite pass locally.
- GitHub parses the workflow and both matrix jobs pass on the pull request head.
- Independent specification and quality reviewers inspect the exact pushed SHA after hosted CI completes.

## Out of scope and follow-up

- Enabling branch protection or repository rulesets. The successful check name must exist before protection can require it.
- Running the machine-local full validator without `--check`; that release process can invoke `uv`, local paths, dependency probes, and evidence regeneration.
- Installing the generated skill shelf or running live providers.
- Merging the pull request; Brent retains merge authority.
