---
name: refine
description: Refine raw mine ore into resolved, contactable leads — the refinery half that the /mine skill defers. Takes a Datamine ore .jsonl, confirms each handle's cross-platform presence with Sherlock, splits likely-orgs from likely-individuals, then resolves the chosen group into identity + contact cards (name, profiles, verified email) with blue-healer. Use when Brent says "refine the ore", "run the refinery", "resolve these handles", "turn ore into leads", or hands over a mine run's JSONL. Sensitive: individual resolution builds PII contact cards — confirm scope first.
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
3. **Confirm + split**:
   `python3 scripts/refine.py classify <ore.jsonl> /tmp/refine-<vertical>/sherlock --out /tmp/refine-<vertical>`
   Writes `confirmed.txt` (≥2 platforms, tune with `--min-platforms`), `individuals.txt`, `orgs.txt`, and prints the breakdown. **Show Brent the split and the counts; let him pick the group.** (See compliance note below.)
4. **Resolve** the chosen group with blue-healer:
   `python3 scripts/refine.py resolve ~/blue-healer /tmp/refine-<vertical>/individuals.txt --out /tmp/refine-<vertical>/contact_cards.json`
   This writes a clean gitignored `app/.env`, launches the Flask app on a free port, POSTs the usernames (`recursive=true, enrich=true`), polls, and downloads `contact_cards.json` (name, location, bio, profiles, candidate emails with deliverability).
5. **Report**: counts resolved, cards with a verified email, and where the JSON landed.

## Compliance — read before resolving individuals

- The mine and signal-atlas draw an explicit line: **public pages only, no individual scraping, org-to-org outreach**. **blue-healer on individuals crosses that line** — it builds per-person contact cards and SMTP-probes mail servers for working emails.
- The SSDI→Allsup model targets **individual claimants** ($500/lead, individuals NOT orgs) — so the individual set is the business target *and* the sensitive one. Both true. **Brent is the compliance authority — surface the split and ask which group; never auto-resolve individuals.**

## Secrets discipline

- Never print, echo, or commit a key value. Reference by name only.
- The clean `app/.env` the helper writes contains only the needed keys and is gitignored (`chmod 600`). Never copy `kloop.env` into a repo.

See [REFERENCE.md](REFERENCE.md) for the gotchas log and the blue-healer `/api` contract. Related: [[mine]] (step 1), the Datamine / Sherlock / blue-healer repos.
