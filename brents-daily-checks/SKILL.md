---
name: brents-daily-checks
description: "Run Brent's complete cross-business daily control panel and return one concise portfolio verdict. Use when Brent says 'daily checks', 'run my daily checks', 'Brent's daily checks', 'morning checks', 'check everything', or asks for the health of all active businesses. Parent orchestrator: integrity first, Alien Probe product-planning, Tiger Claw ops as a separate child, then the rest-of-business list (Money, Mine, Leads, CLAW, WTH, Horror Stories, YouTube longform, YouTube Shorts, Rebuild, Consulting). Do not merge business evidence. If nobody was contacted yesterday the verdict is NO MONEY even if Tiger is green."
---

# Brent's Daily Checks

Run Brent's portfolio-level morning ritual. Keep each business in its own evidence block and return one top-line verdict.

## Boundaries

- Use this skill for generic `daily checks`.
- Use `tigerclaw-daily-checks` directly only when Brent explicitly asks for Tiger or Tiger Claw checks.
- Use `alienprobe-product-puck` directly for Alien Probe product planning.
- Report and flag; do not auto-fix unless Brent separately says `fix it`.
- Ground every live claim at the live surface with a UTC timestamp.
- Never let one child failure prevent an independent, safe child check from running. Mark unavailable children `UNVERIFIED`.
- Never blend Tiger customers, leads, Mine data, or incidents into Alien Probe product evidence.

## 0. Brent's Daily Checks integrity — always first

Read the actual bytes of:

- `/Users/brentbryson/.codex/skills/brents-daily-checks/SKILL.md`
- `/Users/brentbryson/.codex/skills/alienprobe-product-puck/SKILL.md`
- `/Users/brentbryson/.codex/skills/tigerclaw-daily-checks/SKILL.md`
- `/Users/brentbryson/tiger-claw-v4-core/DAILY_CHECKS.md`

Verify the scope split:

1. This parent references both child skills.
2. Tiger's skill and canonical procedure contain no Alien Probe planning step.
3. Alien Probe's skill contains no Tiger operational procedure.
4. Tiger's `daily:checks` package entrypoint exists.
5. All three skill frontmatter blocks contain only `name` and `description`.

Do not run the Python skill-creation validator as a daily operational dependency. That validator is a development-time check and may use its own managed environment. Daily integrity must not fail merely because the system Python lacks PyYAML.

If the split is missing or contradictory, put `BRENT DAILY CHECKS DISARRAY` first in the report. Continue any independent child whose skill is present and readable; never return an all-good verdict.

## 1. Alien Probe — product puck

Load `/Users/brentbryson/.codex/skills/alienprobe-product-puck/SKILL.md` and run **Daily mode**.

Preserve its five lines exactly:

```text
alien_probe_plan  HOLD | ADVANCE | INVESTIGATE
shelf             <live products, prices, and probe result>
buyer_proof       <independent buyers, repeat buyers, verified revenue, or UNVERIFIED>
new_signal        <one meaningful delta or "none">
planning_action   <one bounded research/planning action; never a build action>
```

This is planning and read-only measurement. Do not pay, settle, build, deploy, list, contact a buyer, or touch credentials.

## 2. Tiger Claw — operational health

Load `/Users/brentbryson/.codex/skills/tigerclaw-daily-checks/SKILL.md` and run it end-to-end against its canonical procedure.

Keep its result under a separate `Tiger Claw` heading. A Tiger failure does not change Alien Probe's product verdict, and an Alien Probe `HOLD` does not make Tiger unhealthy.

Tiger `/health` is not a substitute for "FirstTouch actually sent." If health is green and no `sent=` in the last 24h, flag it.

## 3. Rest of business — list (Brent 2026-08-19)

Run after Alien Probe and Tiger. Separate heading. Do not blend these numbers into Tiger or Alien Probe blocks.

Write the filled page to `~/Desktop/HANDOFF/YYYY-MM-DD Daily Check/`.

If nobody was contacted yesterday → verdict **NO MONEY** even if Tiger is green.

| # | Check | Want |
|---|---|---|
| 1 | **Money** | $ in yesterday · conversations · next cash move |
| 2 | **Tiger sends** | FirstTouch / ReferralCadence `sent=` · USAGE_LIMIT / CAP_REACHED |
| 3 | **Mine** | facts/24h · newest fact · 0% pollution · unleased NM pool |
| 4 | **Leads** | new named · contacted · right kind · they answered · next call on calendar |
| 5 | **CLAW** | a stranger (not Brent) commented CLAW and got `https://stan.store/brentbryson/p/5-ai-agents-that-will-3x-your-business` |
| 6 | **WTH** | 3 posts fired on X |
| 7 | **Horror Stories** | NM scar campaign (internal `endless-referrals`) · IG/FB live or scheduled |
| 8 | **YouTube longform** | DEAD DEAL. Report views only. Do not produce, thumb, or publish. |
| 9 | **YouTube Shorts** | public scar Shorts vs unlisted glossary |
| 10 | **Rebuild** | which of 6: CSV export → Tiger import → backup → point at builders → run → log wins |
| 11 | **Consulting** | Pat thread · billed work |

Right-kind lead: NM builder/leader, struggling company or looking for a vehicle. Not Debbie. Not a stadium.
Teaching YouTube: Brent's voice. Second voice only if a few words. Dual-clone format failed the couch test.

Mark any row that could not be grounded `UNVERIFIED`.

## Verdict

Use one of:

- `ALL GOOD`: integrity passes, every child is healthy, rest-of-business has at least one contacted human yesterday, and no grounded failures.
- `NO MONEY`: nobody was contacted yesterday (even if Tiger/Alien Probe look fine).
- `ISSUES`: one or more grounded failures need attention.
- `PARTIAL`: one or more checks could not be grounded.
- `DAILY CHECKS DISARRAY`: the parent/child split or a required procedure contradicts itself.

Report in this order:

```text
BRENT'S DAILY CHECKS — <verdict> — <UTC timestamp>

daily_checks_integrity  <ok | DISARRAY + exact reason>

Alien Probe
<five-line product-puck result>

Tiger Claw
<Tiger daily-check result>

Rest of business
1 Money
2 Tiger sends
3 Mine
4 Leads
5 CLAW
6 WTH
7 Horror Stories
8 YouTube longform
9 YouTube Shorts
10 Rebuild
11 Consulting

first_action            <one bounded next action or "none">
```

Put the most consequential issue first. Do not paste raw logs or secrets unless Brent asks for a specific non-secret excerpt.

## Dependencies

Mandatory:

- all three installed skill files;
- Tiger's canonical `DAILY_CHECKS.md`;
- the Tiger repository `daily:checks` entrypoint; and
- this parent's section 3 list (also on Desktop as `Daily Check List.md`).

Each child owns its own live-service, authentication, and repository dependencies. If a child dependency is unavailable, mark that child's result `UNVERIFIED` and name the exact missing dependency.
