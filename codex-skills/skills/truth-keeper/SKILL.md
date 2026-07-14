---
name: "truth-keeper"
description: "Keep Brent's truth zero-drift across its TWO layers \u2014 the lean universal flyover at ~/Desktop/Truth/ (facts about Brent + things true across ALL projects) and each project's own detail living in its GitHub repo. Guards the boundary between them so neither rots. Use when the user says 'update my docs', 'update the truth', 'refresh the truth', 'keep the truth current', 'the truth is drifted', or right after a build session changed something a doc describes."
---

# Truth Keeper

**The Truth is the single source** — so Brent can *load* it, not re-explain or rebuild
what's already written. Restructured 2026-06-22 into **two layers** after the old
monolith drifted (it tried to be both a universal source AND a project encyclopedia,
so everything got maintained twice). This skill keeps both layers accurate and guards
the line between them.

> Honor the operator's own rules (they live in `The Truth.md` §2 and §5): **## / ###
> headers, bold terms, bullets, NO walls of text**; **establish Ground Truth before
> writing**; **no assumptions, do not look at shapes**; state "updated" only for what
> you verified.

## The model — where truth lives

**Principle: a doc lives as close as possible to the thing it describes.**

- **Universal layer → `~/Desktop/Truth/`** (capital T, LOCAL on the Cheese Grater
  192.168.0.2 — edit directly, no SSH). Holds ONLY facts about Brent or true across
  **all** projects, with no other home. Keep it **small and slow-changing.** The 6 files:
  - `The Truth.md` — master blueprint (TL;DR, mission, operator profile, project portfolio, Pebo Code, coding harness)
  - `General Information.md` — identity/contact/legacy/targets/mandates (**PII — never commit to git**)
  - `F.I.T.FO.md` — operating ethos
  - `What-Is-NuSkin.md` — the business being rebuilt
  - `SKILLS-INDEX.md` — the installed skills in `~/.codex/skills/`
  - `TECH-STACK.md` — roster + repo pointers for shared infra (detail stays in each repo)
- **Project layer → the project's GitHub repo** (`bbrysonelite-max/*`), next to the
  code. All project detail (overviews, internals, status, how-to-run) lives HERE, where
  it physically can't drift from what it describes. This is the single source for that project.
- **`~/Desktop/the-truth-DEPRECATED/`** = the dead old monolith. Its `*_overview.md` /
  `research/` / `Tech Stack/` still need migrating into their repos as each project is
  touched. **Never write to it.** Once a doc lands in its repo, it can be deleted from here.

## Workflow

Make a Codex task checklist item per step.

1. **Decide the layer.** For each thing that may have drifted, ask: *is this universal
   (about Brent / true across all projects, no other home) or project detail?* Universal
   → `Truth/`. Project → that repo. If unsure, it's project detail.
2. **Read what's claimed.** Read the relevant `Truth/` file(s) and/or the project repo
   doc in scope. List the claims that could drift — surfaces, commands, status, paths,
   PRs, dates, counts.
3. **Establish Ground Truth on each claim.** Verify read-only against the *real* source —
   the repo/code (GitHub `bbrysonelite-max/*` or local clone), live system state, your
   own session memory of what just shipped. Don't trust the doc; prove it. For thoroughness,
   spawn a **separate verifier agent** to check claims vs code and report drift.
4. **Update to reality, in the right home.** Universal drift → fix the `Truth/` file.
   Project drift → fix the doc in that repo (branch → PR → verified merge, per §5). Convert
   relative dates to absolute. Smallest honest diff. Keep the formatting mandate.
5. **Guard the boundary.** If project detail has crept into a `Truth/` file → move it to
   the repo and leave only a pointer. If a universal fact is buried in one repo → lift it
   to `Truth/`. Flag (don't silently fix) anything ambiguous.
6. **Report.** What you changed, which layer, what you verified it against, and any claim
   you could NOT verify (named, not hidden).

## Scope
Maintenance, not invention. Don't add projects or rewrite the operator profile unless asked.
**Keep `Truth/` lean** — if a `Truth/` file starts collecting project status/progress, that's
rot; push it to the repo. The cure for the over-and-over habit is **one current universal
source loaded every session + project detail that lives with its code** — never a second copy.

## Codex Runtime

Never expose or print secret, credential, or token values.

Mandatory dependencies:
- `local Truth directory`
- `project repositories`

Preflight each dependency using MCP/app capability discovery, CLI availability/version checks, read-only filesystem or Git checks for repositories, and provider auth-status commands without printing secrets, credentials, or tokens.
If any mandatory dependency is unavailable, stop and report a concise blocked state naming the missing dependency and the next action needed.
