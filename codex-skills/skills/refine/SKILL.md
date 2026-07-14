---
name: "refine"
description: "Refine raw mine ore into resolved, contactable INDIVIDUAL leads \u2014 the refinery half that the /mine skill defers. Takes a Datamine ore .jsonl, confirms each handle's cross-platform presence with Sherlock, DROPS any orgs/lawyers/directories (zero value \u2014 never a deliverable), then resolves the individuals into identity + contact cards (name, profiles, verified email) with blue-healer. Individuals are the only target \u2014 never ask which group. Use when Brent says \"refine the ore\", \"run the refinery\", \"resolve these handles\", \"turn ore into leads\", or hands over a mine run's JSONL."
---

# Refine — turn mine ore into contactable leads

`/mine` finds ore (handle + signal). `/refine` is the next step: **confirm → split → resolve**.

```
ore.jsonl ──Sherlock──> confirmed handles ──split──> individuals / orgs ──blue-healer──> contact cards
```

The helper does the deterministic glue: `scripts/refine.py` (run `python3 scripts/refine.py --help`).

## Prereqs (one-time setup — verify, don't assume)

1. **Keys** in `~/Desktop/GitSync/kloop.env` (+ `~/.config/last30days/.env`): `SERPER_API_KEY`, `SCRAPECREATORS_API_KEY`, `LINKD_API_KEY`, and Oxylabs.
   - **Oxylabs needs `OXYLABS_USERNAME` + `OXYLABS_PASSWORD`** — the Web Scraper API sub-user, **NOT** your account email and **NOT** `OXYLABS_API_KEY`. An email in the username field = HTTP 401.
   - `kloop.env` contains prose lines, so it is **not** shell-sourceable. Parse only `KEY=VALUE` lines (the helper does this). Always verify: `python3 scripts/refine.py envcheck` (loads keys, live-tests Oxylabs auth — prints status, never values).
2. **Sherlock**: `gh repo clone bbrysonelite-max/Sherlock ~/sherlock && uv tool install --python 3.12 ~/sherlock && ln -sf ~/sherlock/scripts/osint ~/.local/bin/osint`. Verify: `sherlock --site GitHub octocat`.
3. **blue-healer**: `gh repo clone bbrysonelite-max/blue-healer ~/blue-healer && cd ~/blue-healer && uv venv --python 3.11 .venv && uv pip install flask flask-cors python-dotenv aiohttp-socks maigret`. (The `.pythonlibs` maigret-path bug is fixed upstream as of PR #1 — a fresh clone works.)

## Workflow

1. **Extract clean usernames** from the ore:
   `python3 scripts/refine.py usernames <ore.jsonl> --out /tmp/refine-<vertical>`
   Drops empty handles (e.g. Quora question rows) and dotted/special handles (poor Sherlock targets).
2. **Sherlock sweep** (background — slow):
   `OSINT_OUTDIR=/tmp/refine-<vertical>/sherlock osint $(cat /tmp/refine-<vertical>/usernames.txt | tr '\n' ' ') --timeout 12 --no-color`
3. **Confirm + drop orgs**:
   `python3 scripts/refine.py classify <ore.jsonl> /tmp/refine-<vertical>/sherlock --out /tmp/refine-<vertical>`
   Writes `confirmed.txt` (≥2 platforms, tune with `--min-platforms`) and `individuals.txt` — the target set. Orgs are auto-detected and **DROPPED** to `orgs_dropped.txt` (a discard log only). **INDIVIDUALS ARE THE ONLY DELIVERABLE.** Organizations, lawyers, and provider directories have ZERO value in this product (Brent's standing rule, 2026-06-29) — never present them, never offer them as a choice, never ask which group. Just report the individuals count and proceed.
4. **Resolve the individuals** with blue-healer:
   `python3 scripts/refine.py resolve ~/blue-healer /tmp/refine-<vertical>/individuals.txt --out /tmp/refine-<vertical>/contact_cards.json`
   This writes a clean gitignored `app/.env`, launches the Flask app on a free port, POSTs the usernames (`recursive=true, enrich=true`), polls, and downloads `contact_cards.json` (name, location, bio, profiles, candidate emails with deliverability).
5. **Report**: counts resolved, cards with a verified email, and where the JSON landed.

## Compliance — settled: individuals ARE the target

- **The deliverable is reachable individuals carrying the signal.** The SSDI→Allsup model targets **individual claimants** ($500/lead, individuals NOT orgs). Orgs / lawyers / provider directories are NOT a valuable deliverable — they are dropped, never offered.
- Brent is the compliance authority and has **already decided**: resolve the individuals. Do **not** re-ask the org-vs-individual question every run — that decision is made. Keep the public-data discipline (only handles that already posted publicly), but the individual set is the whole point of the pipeline. Run the resolve.

## Secrets discipline

- Never print, echo, or commit a key value. Reference by name only.
- The clean `app/.env` the helper writes contains only the needed keys and is gitignored (`chmod 600`). Never copy `kloop.env` into a repo.

See [REFERENCE.md](REFERENCE.md) for the gotchas log and the blue-healer `/api` contract. Related: [[mine]] (step 1), the Datamine / Sherlock / blue-healer repos.

## Codex Runtime

Resolve sibling Codex skills from installed skill roots (including `~/.codex/skills`) or the current collection; do not assume a legacy skill root.

Never expose or print secret, credential, or token values.

Mandatory dependencies:
- `Sherlock and blue-healer repositories`
- `OSINT and enrichment credentials`

Preflight each dependency using MCP/app capability discovery, CLI availability/version checks, read-only filesystem or Git checks for repositories, and provider auth-status commands without printing secrets, credentials, or tokens.
If any mandatory dependency is unavailable, stop and report a concise blocked state naming the missing dependency and the next action needed.
