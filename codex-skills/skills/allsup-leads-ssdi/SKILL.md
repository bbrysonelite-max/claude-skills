---
name: "allsup-leads-ssdi"
description: "Run the monthly Allsup SSDI/SSI lead batch \u2014 the PROVEN process, end to end. Mines active claimants (Reddit + X, last 30 days), tiers them by claim urgency (best/better/good), writes ALLSUP-LEADS-{date}.csv/.md to the Desktop, builds a browsable \"book\" (searchable, tier-filterable HTML), publishes it to a permanent here.now link, and drafts the review email to Pat Sullivan (pat@contatta.com) for Brent to send on to Allsup. Use when Brent says \"run the Allsup leads\", \"SSDI leads\", \"monthly claimant batch\", \"send Pat the leads\", \"run the refinery for Allsup\", or \"pull SSDI claimants\". SSDI-ONLY and reachability-graded \u2014 never resolve individuals or chase emails/phones. For other (non-sensitive) Allsup verticals, build a separate skill; do NOT widen this one."
---

# Allsup Leads — SSDI

The monthly SSDI/SSI claimant batch for the Allsup work (via Pat Sullivan). This skill IS
the proven process — it replaces the `/refine` skill for this vertical. `/refine` (Sherlock
confirm + blue-healer resolve) is the WRONG path here: it collapses the batch and yields ~0
contacts. Use this instead.

**The product:** `handle + distress quote + ≥1 reachable public profile`. Graded on
REACHABILITY, not contact data. Allsup owns all outreach — **we never contact anyone.**

## Quick start

```bash
scripts/run.sh            # pull + tier + rename + build the book (default 30 days)
scripts/run.sh --days 45  # wider window for more volume
```

Then publish the book and draft the email (steps 3–4 below).

## Workflow

1. **Pull + tier + build book** — `scripts/run.sh`. This mines `ssdi-work-fear` on Reddit + X
   (fresh, no ledger), tiers by urgency, writes `~/Desktop/ALLSUP-LEADS-<date>.{csv,md}`, and
   builds `.book/index.html`. Report the tier counts (best/better/good) it prints.
2. **Verify** the CSV has real quotes + profiles (don't ship empty tiers):
   `python3 -c "import csv; r=list(csv.DictReader(open('$HOME/Desktop/ALLSUP-LEADS-<date>.csv'))); print(len(r),'rows; with quote:',sum(1 for x in r if x['quote'].strip()))"`
3. **Publish the book** (permanent, forwardable — Pat sends it to Allsup):
   `~/.codex/skills/here-now/scripts/publish.sh <skill>/.book --client codex`
   Uses Brent's saved here.now key (permanent). Grab the `site_url`.
4. **Draft the email to Pat** (`pat@contatta.com`) via the Gmail tool — DRAFT only, never send;
   Brent reviews and sends. Use the template in [EMAIL.md](EMAIL.md) with this run's counts +
   book URL. Tell Brent to drag `ALLSUP-LEADS-<date>.csv` in as the attachment before sending.

## The rules that make this work (hard-won — do not violate)

- **Reddit is the densest source and is KEYLESS.** Never exclude it. Oxylabs only speeds it up.
- **Grade on reachability, not contact data.** A Reddit/X profile IS a reachable channel.
- **NEVER run the heavy resolver** (blue-healer maigret / email-finder / SMTP). On pseudonymous
  handles it yields ~0, burns API calls, and creates PII/compliance exposure. The lean pull IS
  the product. (This is why `/refine` is wrong for SSDI.)
- **No emails/phones.** They aren't findable for these handles and aren't the deliverable. The
  profile is the channel — Allsup DMs it. Say this plainly to Pat (see EMAIL.md).
- **SSDI only.** Other Allsup lead types are a different, non-sensitive vertical — build a
  separate skill for them; don't add them here.

## Tiers (encode claim urgency)

- **best** — denied / appeal / reconsideration / hearing / overpayment / can't work
- **better** — applying / pending / waiting / nervous
- **good** — work-incentive / Ticket-to-Work / "will working cost my benefits"

## Paths & deps

- Proven pull: `~/Desktop/Datamine/blue-healer/Datamine-repo/scripts/allsup_pull.py`
- Datamine bin: `~/Datamine/.venv/bin/datamine` (auto-set as `DATAMINE_BIN`)
- Publisher: `~/.codex/skills/here-now/scripts/publish.sh` (Brent's key already saved)
- Canonical background: `ALLSUP_RUNBOOK.md` in the Datamine-repo; memory
  `project_ssdi_allsup_proven_pipeline_runbook`.

## Codex Runtime

Resolve sibling Codex skills from installed skill roots (including `~/.codex/skills`) or the current collection; do not assume a legacy skill root.

Never expose or print secret, credential, or token values.

Mandatory dependencies:
- `Datamine environment`
- `last30days data-source credentials`
- `here.now publishing credentials`

Preflight each dependency using MCP/app capability discovery, CLI availability/version checks, read-only filesystem or Git checks for repositories, and provider auth-status commands without printing secrets, credentials, or tokens.
If any mandatory dependency is unavailable, stop and report a concise blocked state naming the missing dependency and the next action needed.
