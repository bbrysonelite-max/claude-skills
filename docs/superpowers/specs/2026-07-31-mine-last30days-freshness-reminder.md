# Mine Last30Days Freshness Reminder Specification

## Purpose

Every invocation of the `mine` skill must keep the market-selection input fresh. Last30Days helps decide **what is worth mining**; Datamine executes the selected vertical; the refined leads are the commercial product.

## Required behavior

1. Before the Mine run instructions, the skill must visibly remind Brent to check or update the installed Last30Days skill from its upstream project before relying on Last30Days research to choose a vertical.
2. The reminder must occur on every `mine` skill invocation. It must not be hidden in optional notes or only appear for new verticals.
3. The reminder is non-blocking when a vertical is already selected: surface it, then continue the approved Mine workflow.
4. The reminder must not claim that Last30Days is current unless freshness was actually verified.
5. The reminder must not silently install or update Last30Days, mutate credentials, or print secret values. Updating the dependency is a separate explicitly authorized action.
6. The reminder must preserve the product boundary: Last30Days supplies recent market-selection intelligence, Mine produces raw ore, and the refinery produces commercially valuable leads.
7. The canonical source is `mine/SKILL.md`. The generated Codex copy, `codex-skills/skills/mine/SKILL.md`, must be produced by the deterministic builder rather than edited directly.

## Fixed reminder text

The operational instruction must include this visible sentence:

> **Last30Days freshness reminder:** Before relying on Last30Days to choose what to mine, check or update the installed skill from `https://github.com/mvanhorn/last30days-skill`. Do not silently update it; if the vertical is already selected, show this reminder and continue.

Additional explanation may surround the sentence, but its meaning and every-run placement must not weaken.

## Acceptance proof

- An independent test author demonstrates that the pre-change skill omits the contract and commits tests without editing production skill files.
- A separate implementer edits the canonical Mine skill and runs the builder to regenerate the Codex copy.
- Tests verify the fixed reminder and product boundary in both canonical and generated copies.
- `python3 codex-skills/scripts/build.py --check` passes from the repository root.
- `python3 -m unittest discover -s tests` passes from `codex-skills/`.
- Independent specification and code-quality reviewers inspect the exact pushed PR head after CI or GitHub checks complete.

## Out of scope

- Updating the Last30Days dependency itself.
- Running live Last30Days research or a live Mine batch.
- Changing Datamine code, provider credentials, environment files, lead scoring, or refinery behavior.
- Merging either repository's pull request; Brent retains merge authority.
