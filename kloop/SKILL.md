---
name: kloop
description: Optimize a text asset (system prompt, outreach copy, onboarding screen, follow-up sequence) against a measurable score using the Karpathy loop in ~/Auto-Research-Loop. A Generator LLM proposes a change, a Target LLM runs it, a Judge LLM scores it, and only improvements that beat the safety margin are kept. Use when Brent says "kloop", "run the loop", "optimize this prompt", "tune this copy", "stop guessing at this wording", or when an asset is about to ship on opinion rather than measurement.
---

# kloop — the optimizer

Turns text we wrote by guess into text that was measured. Repo: `~/Auto-Research-Loop`. Channel: `#kloop`.

## Quick start

```bash
~/.claude/skills/kloop/scripts/kloop-run.sh ~/Auto-Research-Loop/experiments/<name>
```

The script wires three different providers to the three roles and fails loudly if a key is missing. Add `--dry-run` to print the resolved config without spending anything.

## A workspace needs three files

| File | What it is |
|---|---|
| `program.md` | The brief — what "better" means. The Generator reads this. |
| `<asset>` | The thing being optimized (`candidate_prompt.txt`, `message.txt`…). This file gets rewritten. |
| `eval.mjs` | Prints `score: <number>`. Default eval command; override with `--eval`. |

Optional: `rubric.json` (`--rubric`), `scenarios.json` (`--scenarios`). Backups land in `.kloop-backup/`.

Scaffold a new one from a sentence:

```bash
node ~/Auto-Research-Loop/cli/kloop.mjs --dir ./new-project --api-key <key> \
  --scaffold "Optimize the first-touch message for a Thai network-marketing leader"
```

## Workflow

1. **Write `program.md` first.** If you cannot say what better means, the loop cannot find it.
2. **Write the rubric to score Brent's standards** — see `rubric-standards.md`. Not generic quality.
3. **Dry-run.** Confirm three distinct providers before spending.
4. **Run.** Start `--max-iter 5`. Read `results.json`.
5. **Report the winner as a CANDIDATE.** A judge score is not a customer. Brent decides what ships.
6. **Log it to `#kloop`** with the score delta and what was NOT proven.

## Rules

- **Three different model families.** Same family in all three seats inflates the score — the repo's README says so, and so does `kloop.env`. The run script enforces it.
- **Never auto-deploy a winner.** The loop optimizes against a judge, not against a customer.
- **`--safety-margin` exists because evals are noisy.** Default `0.06`. Do not lower it to manufacture a win.
- **Commit the results.** The 2026-04-27 voice-training run was never committed and its findings were lost in the working tree. Do not repeat that.
- Say what the run did not establish. A higher score on a rubric is not evidence of revenue.

## What to run it on

Priority order lives in the `#kloop` channel canvas. Worst-guess first: agent system prompts, outreach first-touch, onboarding copy, Tiger follow-up sequences, episode hooks.

## Reference

- Rubric that encodes Brent's standards: [rubric-standards.md](rubric-standards.md)
- Full flag list: `node ~/Auto-Research-Loop/cli/kloop.mjs --help`
