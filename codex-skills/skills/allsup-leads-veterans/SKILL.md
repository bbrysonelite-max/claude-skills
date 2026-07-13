---
name: "allsup-leads-veterans"
description: "Run the Allsup VETERANS benefits-gap lead batch \u2014 same proven process as the SSDI skill, tuned for veterans. Mines veterans who are owed VA benefits but not getting them \u2014 never filed / didn't know they qualified, denied or under-rated, or newly eligible under the PACT Act (burn pit / Agent Orange / toxic exposure) \u2014 from Reddit + X + TikTok (last 30 days), tiers by need, writes VETERANS-LEADS-{date}.csv/.md to the Desktop, builds a browsable book, publishes it to a permanent here.now link, and drafts the email to Allsup (via Pat Sullivan) for Brent to send. Use when Brent says \"run the veterans leads\", \"veteran leads\", \"VA benefits leads\", \"PACT Act leads\", or \"veterans batch for Allsup\". Reachability-graded \u2014 never resolve individuals or chase emails/phones. Sibling of allsup-leads-ssdi; keep the two separate."
---

# Allsup Leads — Veterans

The veterans benefits-gap batch for Allsup. Same customer, same proven process as
[allsup-leads-ssdi], different vertical + tiers. **The product:** `handle + own-words quote +
≥1 reachable public profile`. Graded on REACHABILITY, not contact data. Allsup owns all
outreach — **we never contact anyone.**

**The signal:** veterans who DESERVE VA benefits but aren't getting them —
- **never filed / didn't know they qualified** (a huge, findable population)
- **denied or under-rated**, fighting for what they're owed
- **newly eligible under the PACT Act** (burn pit / Agent Orange / Camp Lejeune / Gulf War) and unaware.

## Quick start

```bash
scripts/run.sh            # pull + tier + build the book (default 30 days)
scripts/run.sh --days 45  # wider window for more volume
```

Then publish the book and draft the email (steps 3–4).

## Workflow

1. **Pull + tier + build book** — `scripts/run.sh`. Mines `veterans-benefits-gap` on
   Reddit + X + TikTok (fresh, no ledger), tiers by need, writes
   `~/Desktop/VETERANS-LEADS-<date>.{csv,md}`, builds `.book/index.html`. Report the tier counts.
2. **Verify + eyeball** the CSV. TikTok can leak the occasional creator/coach (they talk *about*
   veterans, not as one) despite the first-person + handle filters — glance at the BEST tier and
   drop any obvious creator/caregiver rows before sending. If TikTok is too noisy for a given run,
   re-run pulling only Reddit + X (edit `SURFACES` in `scripts/veterans_pull.py`).
3. **Publish the book** (permanent, forwardable):
   `~/.codex/skills/here-now/scripts/publish.sh <skill>/.book --client codex`
4. **Draft the email** via the Gmail tool — DRAFT only, never send. Use [EMAIL.md](EMAIL.md) with
   this run's counts + book URL. Tell Brent to drag `VETERANS-LEADS-<date>.csv` in as the
   attachment. (Recipient: Allsup's David `d.doeren@allsup.com`, or Pat `pat@contatta.com` —
   ask Brent which for this run.)

## The rules (same as SSDI — do not violate)

- **Reddit is densest and KEYLESS.** Oxylabs only speeds it up. Never exclude Reddit.
- **Grade on reachability**, not contact data. A Reddit/X/TikTok profile IS a reachable channel.
- **NEVER run the heavy resolver** (blue-healer maigret / email-finder / SMTP). Yields ~0 on
  pseudonymous handles, burns API calls, creates PII exposure. The lean pull IS the product.
- **No emails/phones** — not findable, not the deliverable. The profile is the channel.
- **Veterans only.** Keep separate from the SSDI skill; don't merge the two.

## Tiers (encode need)

- **best** — denied / appealing / under-rated / 0% / never filed / owed back pay
- **better** — filing / gathering evidence / C&P exam / secondary condition / intent to file
- **good** — eligibility / PACT Act / rating questions

## Paths & deps

- Vertical: `~/Datamine/datamine_config/verticals/veterans-benefits-gap.yaml` (edit phrases/subs here)
- Pull + book: self-contained in this skill's `scripts/` (`veterans_pull.py`, `build_book.py`)
- Datamine bin: `~/Datamine/.venv/bin/datamine` (auto-set as `DATAMINE_BIN`)
- Publisher: `~/.codex/skills/here-now/scripts/publish.sh` (Brent's key already saved)

## Codex Runtime

Resolve sibling Codex skills from installed skill roots (including `~/.codex/skills`) or the current collection; do not assume a Claude skill root.

Never expose or print secret, credential, or token values.

Mandatory dependencies:
- `Datamine environment`
- `last30days data-source credentials`
- `here.now publishing credentials`

Preflight each dependency using MCP/app capability discovery, CLI availability/version checks, read-only filesystem or Git checks for repositories, and provider auth-status commands without printing secrets, credentials, or tokens.
If any mandatory dependency is unavailable, stop and report a concise blocked state naming the missing dependency and the next action needed.
