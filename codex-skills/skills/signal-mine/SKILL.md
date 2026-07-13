---
name: "signal-mine"
description: "Run the signal-mining pipeline \u2014 find public evidence of demand, fear, confusion, and intent before people become leads, then map communities, creators, and partner orgs with the safest contact path for each. Use when Brent says \"signal mine\", \"run the signal mine\", \"mine signals\", asks to refresh the Contatta/Pat org map, or starts demand-signal research for a new vertical."
---

# Signal Mine

Signal mining = finding public conversations where people reveal the problem
before they become a lead. We mine MEANING (what fear, how often, what exact
words, is there a contact path) — we never scrape individuals.

## Pipeline status (LIVING SECTION — update after every proven run)

| Track | Status | Last run | Output |
|-------|--------|----------|--------|
| 5 — Provider orgs (SSA directory) | PROVEN | 2026-06-10: 512 orgs scored, 224 enriched, 221 with contact path | `org_rows.csv`, `outreach_ready.csv` |
| 1 — Reddit fear-phrase mining | PROVEN | 2026-06-10: 83 signal threads (5 score-10, 16 score-8); density = r/disability 21, r/SSDI_SSI 18, r/SSDI 16, r/SocialSecurity 15 | `track1_reddit.csv` |
| 2 — YouTube creators | PROVEN | 2026-06-10: 54 signal videos (7 score-10, 31 score-8), 29 partner-tier; 9 channels with 2+ signal videos | `track2_youtube.csv` |
| 3 — Facebook groups | PROVEN (discovery) | 2026-06-10: 9 groups via Codex web search; member counts/admin paths MANUAL (login wall confirmed via scrapling) | `track3_facebook.csv` |
| 4 — Quora/forums | PROVEN | 2026-06-10: 17 questions (11 score-10); top pages confirmed answer-rich via scrapling stealth | `track4_quora.csv` |

All five tracks proven for the ssdi-work-fear vertical. Serper key live as of
2026-06-10 (free tier, 2,500 queries; paid credits expire 6 months after
purchase). Re-run cadence is operator's call (tracks 1/2 are cheap to refresh
monthly; Track 5 quarterly — the SSA directory moves slowly).

## Setup (every run)

1. Load the vertical config. Default: `verticals/ssdi-work-fear.md` (Contatta/Pat gig).
   For a new vertical, ask Brent for fear/intent phrases first, write a new
   verticals file, then proceed.
2. Workdir: `~/Desktop/signal-mine/` (create if missing). All output CSVs land there.
3. Keys live in `~/.config/last30days/.env` (ScrapeCreators, xAI) and
   `~/Desktop/GitSync/kloop.env` (Supabase, OpenAI). Never print values.
4. Scoring rubric + data model: see [REFERENCE.md](REFERENCE.md). Every mined
   item becomes one row in those columns.

## Track 5 — Provider/source orgs (fully scripted)

```bash
WORKDIR=~/Desktop/signal-mine
bash scripts/fetch_ssa_directory.sh "$WORKDIR"        # 4 JSON pulls from choosework.ssa.gov
python3 scripts/build_org_rows.py "$WORKDIR"          # -> org_rows.csv, scored
# enrichment needs scrapling: use $WORKDIR/.venv (create + pip install 'scrapling[all]' if missing)
"$WORKDIR/.venv/bin/python" scripts/enrich_contacts.py "$WORKDIR"  # -> outreach_ready.csv
```

Run enrichment in the background (5-15 min, resumable via enrich_log.jsonl).
Deliverable: `outreach_ready.csv` — every score>=8 org with best_contact_path.

## Track 1 — Reddit (scripted)

```bash
"$WORKDIR/.venv/bin/python" scripts/track1_reddit.py "$WORKDIR"   # -> track1_reddit.csv
```

RSS only — search.json is 403 from this network. The script searches each
fear phrase site-wide plus 3 queries per target sub, scores on the 10/8/6
rubric, and approximates comment counts for score>=8 threads via thread RSS.
Known gotchas: a nonexistent sub (e.g. r/Ticket2Work) silently returns a junk
global feed — entries dated years ago with empty subreddit terms are the tell;
r/SSI 404s (banned/private). The dense communities for this vertical:
r/disability, r/SSDI_SSI, r/SSDI, r/SocialSecurity.

## Track 2 — YouTube (scripted, ScrapeCreators)

```bash
python3 scripts/track2_youtube.py "$WORKDIR"   # -> track2_youtube.csv
```

Uses SC endpoints `/v1/youtube/search?query=` and `/v1/youtube/video/comments?url=`
(auth header `x-api-key`; key in last30days .env). Comment text lives in the
`content` field, NOT `text`. Scores titles on the signal rubric, rolls up
channel density (2+ signal videos = partnership 9), extracts question-shaped
comments as "common questions". ~16 SC credits per run.

## Tracks 3+4 — Facebook groups & Quora/forums (discovery scripted-ish)

Discovery via Serper (key: `SERPER_API_KEY` in `~/Desktop/GitSync/kloop.env`,
verified live 2026-06-10): `POST https://google.serper.dev/search` with header
`X-API-KEY: <key>` and JSON body `{"q": "<query>", "num": 10}` — organic
results in `.organic[]`, 1 credit/search. Codex web search is the fallback if the
key ever dies. Queries: `site:facebook.com/groups "<phrase>"` and
`site:quora.com "<phrase>"`.
`scripts/track34_build.py` holds the 2026-06-10 discovery snapshot inline and
the CSV/enrichment shape — for a re-run, refresh the FB_GROUPS/QUORA lists
from new discovery, then run with `--enrich-quora`.

Proven findings (2026-06-10): logged-out Facebook shows ONLY the login shell
(title "Facebook", no og:title, no member counts) even via scrapling stealth —
group names/member counts/admin paths are strictly manual. Quora renders
full answer pages logged-out via StealthyFetcher with network_idle=True;
there is no explicit answerCount in the HTML — count `q-box qu-userSelect--text`
blocks as a page-richness indicator (~40 = answer-rich), not a literal answer
count. A group URL recurring across multiple discovery queries = density
signal; count recurrences per group.

## Hard rules

- Public pages about communities and orgs ONLY. No member scraping, no
  automated DMs, no individual profiles. The deliverable is a MAP, not a list
  of people.
- Pace org-site crawls (8 workers max, 20s timeouts). Government APIs: 2s
  sleep between pulls.
- Present results as: counts by score tier, contact-path breakdown, top
  outreach targets. Keep Pat-facing framing: "signal mining public
  conversations, not scraping disabled people."

## Output

All tracks append to the workdir as CSVs matching the REFERENCE.md data model.
When Brent asks for Pat-visible output, push rows to Supabase (key in
kloop.env) or hand him the CSV.

## Codex Runtime

Resolve sibling Codex skills from installed skill roots (including `~/.codex/skills`) or the current collection; do not assume a legacy skill root.

Never expose or print secret, credential, or token values.

Mandatory dependencies:
- `source APIs and credentials`
- `Python script dependencies`

Preflight each dependency using MCP/app capability discovery, CLI availability/version checks, read-only filesystem or Git checks for repositories, and provider auth-status commands without printing secrets, credentials, or tokens.
If any mandatory dependency is unavailable, stop and report a concise blocked state naming the missing dependency and the next action needed.
