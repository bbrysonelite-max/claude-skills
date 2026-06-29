---
name: mine
description: Run the agnostic Data Mine against a vertical — find raw "ore" (people/orgs showing a signal) from the configured surfaces over the last 30 days. Use when Brent says "run the mine", "mine <vertical>", "run the data mine against <X>", or wants raw leads for a vertical (e.g. ssdi-work-fear, network-marketers). The mine finds ore; the refinery grades it into high-value leads (separate step).
---

# Mine — run the agnostic Data Mine

One job: run `datamine` against a named vertical and show the ore. It's a one-liner.

## Run it

The Data Mine is the `Datamine` package — GitHub `bbrysonelite-max/Datamine`, and on the iMac at `~/Datamine` (`2020iMac.local`, SSH `brentbryson` w/ `~/.ssh/trashcan`).

```bash
# from the repo (clone it if you don't have it: gh repo clone bbrysonelite-max/Datamine)
cd ~/Datamine
[ -d .venv ] || { python3 -m venv .venv && .venv/bin/pip install -q -e .; }
# Reddit hard-rate-limits a single IP (429s). Pull the Oxylabs residential-proxy
# creds from Secret Manager so the mine routes Reddit through them and runs fast
# (~80s vs 25+ min). No-op if not gcloud-authed — it falls back to direct fetch.
export OXYLABS_USERNAME="$(gcloud secrets versions access latest --secret=oxylabs-username 2>/dev/null)"
export OXYLABS_PASSWORD="$(gcloud secrets versions access latest --secret=oxylabs-password 2>/dev/null)"
.venv/bin/datamine --vertical <vertical-name> --out /tmp/mine-<vertical-name>
```

- `<vertical-name>` = any file in `datamine/verticals/` (e.g. `ssdi-work-fear`). To target a NEW group, add a `datamine/verticals/<name>.yaml` (build phrases, fear phrases, keywords, per-surface queries) — no code change.
- Output: `/tmp/mine-<name>.csv` / `.jsonl` / `.md` — **raw ore**, one row per person: source, handle, url, build/fear signal, date, found_via, text. NOT enriched leads (no name/email/phone — that's the refinery). CSV is spreadsheet-safe; **JSONL is the raw feed for the refinery**.
- After the run: report the count and the by-source / by-signal breakdown. Hand the JSONL to the **refinery**, or the CSV to Brent.

## Notes

- 6 surfaces run by default: Reddit (Oxylabs), YouTube + TikTok (ScrapeCreators), X (xAI Grok), Quora (Serper), Hacker News. Keys auto-load from `~/.config/last30days/.env` + `~/Desktop/GitSync/kloop.env`; Oxylabs is exported from Secret Manager above.
- **Ledger** (`~/.datamine/<vertical>.json`): re-runs skip already-mined people and dead surfaces. Use `--no-ledger` for a full fresh run; `--ledger <path>` to override.
- **The mine finds ore; the refinery turns ore into the diamond** — identity (maigret/blue-healer) → contact → qualified. Different, gated step. See [[the-rebuild]].
- Override surfaces/window if needed: `--surfaces reddit youtube --days 14`.
