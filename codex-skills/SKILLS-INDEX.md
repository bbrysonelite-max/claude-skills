# Skills Index

> **Cut 2026-09-26** on Brent's word: `bbrysonelite-max/claude-skills` PR #27, squash `83d5b14`. **129 → 41 skills, 270k → 49k lines.** Pulled to every checkout the same night (cheesegrater `~/.claude/skills` and `~/claude-skills`, iMac both; MEASURED 2026-09-26T03:54Z). The shelf `~/.claude/skills` on each Mac IS a git checkout of that repo — `git pull --ff-only` is the sync.
> Removed: the doc-drift skills (context/doc/tiger-doc/truth keepers, vault-hygiene, skills-librarian, skill-miner, optimize, unfinished, closing-ritual), Tiger ops (ship-it, tigerclaw-daily-checks, system-status-triage, production-debugging-loop, page-rethink), dead tooling (gitnexus-*, claude-memory-*, gws-*), four vendored blobs (brag, last30days, here-now, tiger-whitepaper), seven of nine audit skills, and every duplicate copy (`promoted/`, `overrides/`, `archived-sources/`).
> Untracked extras still on the cheesegrater shelf, not in the repo: `critic-gate`, `herdr`, `macos-harness`, `phone-harness`, `skill-shipper`, `synced/`.

## Doctrine (4)
- **ground-truth** — the ladder: only rungs 4 (MEASURED) and 5 (VERIFIED) are truth.
- **the-loop** — the build pipeline with role separation.
- **tiny-team** — one human + separated agent roles.
- **fitfo** — behave like an ant; never "I can't" without three routes.

## Mechanical (4)
- **loading-secrets** — 1Password via `opa` before asking Brent anything.
- **jumbo-health** — health check of the memory system.
- **visit-jumbo** / **visit-jumbo-deep** — session-opening grounding from Jumbo.

## Kept on his word (1)
- **cloud-run-reauth** — gcloud access to the Tiger GCP project (needed until it's turned off).

## Quality (2)
- **failure-modes** — FMEA / pre-mortem sweep.
- **blind-spots-audit** — what Brent isn't asking.

## Leads & money (9)
- **allsup-leads-ssdi** · **allsup-leads-veterans** — the monthly Allsup batches, proven process.
- **blueprint** · **mine** · **refine** · **signal-mine** · **whitelabel-radar** · **network-reactivator** · **intro-page**

## Video (10) — used daily
- **brag-machine** · **brag-one** · **brag-two** · **brag-week** · **brag-music** · **brag-voice** · **brag-personal**
- **longform-video** · **watch** · **hyperframes-audio**

## Brand & campaigns (4)
- **two-brents-brand** · **wth-campaign** · **beacon-protocol** · **alienprobe-product-puck**

## Running the office (4)
- **brents-daily-checks** · **brent-office-manager** · **desktop-delivery** · **i-have-adhd**

## Tools (3)
- **agent-reach** · **graphify** · **kloop**

**Total: 41.** Harness scripts that replaced the doc-drift skills live in `Lessons-to-Learn/harness/` (claim-guard.py Stop hook, sabotage.sh, no-fakes.sh, LADDER.md).
