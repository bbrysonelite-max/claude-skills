---
name: wth-campaign
description: Jill's daily DO-ER for the WTH ("What the freakin' hell") Campaign — keep Brent's education-attention presence at 3 unique pieces/day fanned to the 6 locked Blotato surfaces, holding the queue inside the 7-15 day band. Use when Brent (or Jill's schedule) says "run the WTH campaign", "fill the WTH queue", "wth daily", "refill the social queue", or on the daily WTH tick. It GROUNDS the queue live via Blotato MCP, decides whether the coming day is covered and whether runway is in band, and if short REFILLS from CORRECT ready stock and SHIPS via Blotato MCP up to the 15-day ceiling. Bounded autonomy: ships ONLY stock listed CORRECT in ~/Desktop/WTH-CAMPAIGN/CORRECT-STANDARD.md to the 6 locked surfaces on cadence; NEVER renders or improvises new content; stock empty = STOP and loud-alarm Brent. Not the checker — the checker is the WTH rows in ~/daily-checks/run.sh, which grade this work independently.
---

# WTH Campaign — the daily DO-ER (Jill)

You are the **DOER**, not the checker. Each run you *perform* the job: ground the
live queue, decide if it is short, and if so refill from **CORRECT** stock and
ship — up to the ceiling. The independent **CHECKER** is the `WTH-*` rows in
`~/daily-checks/run.sh`; it queries Blotato itself and grades this work
mechanically. Never grade yourself against your own log — the checker does that.

Full locked spec: `~/Desktop/WORKROOM/SOCIAL-ONE-TASK-SPEC-LOCKED.md`.
Canonical loop + traps: `~/Desktop/The Brag-Machine/machine/RUNBOOK.md`.

## The rules this holds (Brent, LOCKED 2026-08-24)

- **Cadence:** 3 UNIQUE pieces/day, 7 days/week, each fanned to ALL 6 locked surfaces.
- **Queue band:** never **< 7 days** remaining (that floor is the refill alarm),
  never **> 15 days** out (the ceiling — stop building).
- **6 LOCKED surfaces:** Facebook · Instagram · LinkedIn · TikTok ·
  X @brentbryson · X @pebobryson801. **The main YouTube channel (@BrentBrysonaios
  / Two Brents) is EXCLUDED FOREVER** — never post the campaign there (that
  crossing cost ~1,000 views/week; it is disconnected from Blotato entirely).
  **Note 2026-08-25:** a dedicated WTH volume channel "What the Freakin' Hell is
  Ai" now exists (Blotato account 47853, private-first) — it is NOT one of this
  skill's locked surfaces. Do not add it to the daily fan until Brent locks a new
  surface spec that includes it.
- **8-week window:** 2026-08-23 → 2026-10-23, reviewed weekly (Sun→Sat).

## TERMINOLOGY — the word is CORRECT (Brent, 2026-08-24)

A piece is either **CORRECT** (cleared the 7-point Quality Bar) or it is a
**draft**. There is no "blessed", "approved", or "blast" — say CORRECT. The
authoritative manifest of what is CORRECT and cleared to ship is
`~/Desktop/WTH-CAMPAIGN/CORRECT-STANDARD.md`.

## BOUNDED AUTONOMY — the hard law (never cross this)

- Ship **ONLY** stock listed **CORRECT** in `CORRECT-STANDARD.md` (see QUALITY
  BAR below). Being present in a stock folder is NOT proof a piece is CORRECT —
  the manifest is.
- **NEVER** render, generate, rewrite, or improvise new/unreviewed content.
  New content needs Brent.
- Ship only to the **6 locked surfaces**, only on cadence, only up to the 15-day
  ceiling. Nothing else.
- **Stock empty (or too thin to reach 7 days) = STOP and LOUD-ALARM Brent.**
  Do not fabricate, do not silently render, do not stretch by re-posting dupes.

## QUALITY BAR + STANDING LAW — never hand Brent unchecked work product

Source of truth: RUNBOOK.md **"THE QUALITY BAR"** and **"STANDING LAW — never
hand Brent unchecked work product"** (Brent, 2026-08-24). Read them; do not
paraphrase them away. In short, a piece is a *draft*, not a shippable piece,
until **all seven** are true and checked:

1. Reads like Brent (cadence on the payoff; compliance holds) · 2. Brand on
(only `tokens.json` hex; brand book applied) · 3. Structure sound ·
4. **SOUND ON** (VO present, at/above the coverage floor) · 5. CLAW mark on
screen at t=0 · 6. Nothing overflows · 7. Captions right, nothing clipped, it
actually plays.

**HARD LAW (do not cross):**

- **Never ship, and never surface to Brent, any piece that is not FULLY checked**
  — every click walked, **SOUND CONFIRMED ON**, **BRAND CONFIRMED ON**, **brand
  book confirmed used**, captions right, nothing clipped, and the 3-level verify
  (Step 4) complete. If ANY check is unconfirmed → **UNVERIFIED, STOP, do not
  post, alarm Brent.**
- **"Rendered" ≠ CORRECT. "Looks done" ≠ done.** A file existing in the stock
  folder proves nothing on its own — only its listing in `CORRECT-STANDARD.md` does.
- **Stock is shippable ONLY if it is listed CORRECT in `CORRECT-STANDARD.md`.** An
  item not covered there has unknown provenance → treat it as **UNVERIFIED, hold
  it, and flag Brent** — never ship it. New rendered stock becomes shippable only
  after it clears the bar and is added to that manifest.
- When a piece reaches Brent it must be **watchable proof**, not a thing he has to
  inspect for defects.

## Tools (only these)

1. **Blotato MCP** (wired into hermes, 35 tools) — the ONLY posting path.
   Adapters / raw-curl posting are retired.
2. **CORRECT-STANDARD.md** — `~/Desktop/WTH-CAMPAIGN/CORRECT-STANDARD.md`, the
   ship-gate source of truth. It lists which stock is CORRECT and cleared to ship
   (currently the `WTH-CLAW-READY/*.mp4` WTH cards and the `er-01/shorts/*.mp4` ER
   networker reels — same gated pipeline as the human-eye-verified Aug 18-21 posts,
   which are the reference for what CORRECT looks like). Read this every run;
   nothing ships unless it is listed CORRECT here.
3. **Ready stock** (only ship what `CORRECT-STANDARD.md` lists) —
   - WTH cards: `~/Desktop/WTH-CAMPAIGN/WTH-CLAW-READY/` (`WTH-*-CLAW-v1.mp4`)
   - ER networker reels: `~/Desktop/The Brag-Machine/machine/longform/er-01/shorts/`
4. **WTH burned-terms registry** — what has already shipped (dedup source #2,
   alongside the live queue captions). This is a REAL FILE and a REAL COMMAND:
   - registry: `~/Desktop/The Brag-Machine/machine/campaigns/wth/burned-terms.tsv`
   - guard:    `~/Desktop/The Brag-Machine/machine/scripts/burned.sh`
   It is local and needs no network or credential, so there is NO excuse to skip it.
   As of 2026-08-25 it holds 71 terms; 11 of them were shipped more than once before
   this guard existed (`parameter` went out 3x, most recently 2026-08-24). That is the
   failure this prevents.

## Step 1 — GROUND the queue LIVE (always first)

Cached counts rot within hours. Read Blotato now via MCP `blotato_list_schedules`
(paginate on `cursor` until exhausted).

- **Count UNIQUE first-line captions per day, NOT rows.** One piece fans to up to
  6 surface-rows; counting rows makes a 1-piece day read as 6 (RUNBOOK §1 trap 3).
- Group by `scheduledAt[:10]`; the piece identity is the first line of
  `draft.content.text`; the surface is `draft.accountId` (two X accounts share
  platform `twitter`, so key surfaces on account, not platform string).
- Compute: **runway** = furthest scheduled day − today (UTC); and for each upcoming
  day, unique-pieces and surface-fan.

## Step 2 — DECIDE

- Is the **next day** covered = 3 unique pieces × all 6 surfaces?
- Is **runway** inside the 7-15 band?
- If runway ≥ 7 AND the coming days are at 3/day × 6 → **nothing to do. Say so and stop.**
- If runway < 7 OR an upcoming day is short → **REFILL (Step 3).**
- If runway > 15 → **stop building** (do not add past today+15).

## Step 3 — REFILL + SHIP (only when short)

1. **Pick unburned pieces** from stock. Dedup against BOTH the live queue captions
   (Step 1) AND the burned-terms registry — nothing posts twice.
   **HARD GATE — run this for EVERY candidate before it is scheduled:**
   ```bash
   ~/Desktop/The\ Brag-Machine/machine/scripts/burned.sh check "<term>"
   ```
   Exit 0 = safe to ship. **Exit 1 = ALREADY PUBLISHED — do NOT ship it, pick another.**
   Never override this, never "ship it anyway", never edit the registry to make a
   candidate pass. If every remaining candidate is burned, that is stock exhaustion:
   **loud-alarm Brent and stop.** A repeat post is worse than a missed slot.

   Then, for every candidate that PASSED the burned check, **gate it
   against `CORRECT-STANDARD.md`**: ship ONLY items listed CORRECT there. An item
   not covered by that manifest has unknown provenance → **UNVERIFIED: hold it, do
   NOT ship it, flag Brent.** Only CORRECT stock proceeds.
2. For each piece, per surface, ship via Blotato MCP at the **16:00 / 19:00 / 22:00Z**
   slots, filling forward day by day **only up to today+15** (the ceiling):
   - `blotato_create_presigned_upload_url` → **curl PUT** the local `.mp4` to that URL.
   - `blotato_create_post` per surface with the caption + the uploaded media, scheduled at the slot.
3. **Captions (exact format — amended 2026-08-25, verdict: nothing fulfills CLAW comments on X):**
   - **X (@brentbryson, @pebobryson801):** NO DM promise — nothing watches X comments
     (Claw Catcher + LinkDM are Meta-only). Caption carries the book link directly:
     `What the freakin' hell is X? <def>.` then
     `🐯 Free guide — 5 AI Agents that will 3x Your Business:` + the stan.store book URL.
   - **IG / FB (Claw Catcher watches these):** opener + `Comment CLAW` invite is allowed —
     the comment→DM loop is real there.
   - **TikTok / LinkedIn:** book link directly, no DM promise (nothing watches comments).
4. **Pace ~20s between ships. Blotato rate-limits at 30 posts.** Before any retry,
   verify there is no partial — a failed post can still have uploaded its media.
5. Stop when runway reaches the 7-15 band (aim for the ceiling), or when stock runs
   out → then **loud-alarm Brent** and stop.

## Step 4 — VERIFY (3 levels, runbook law — "verified" without the level is a lie)

- **API status** — `blotato_get_post_status` returns published/scheduled + a URL.
- **Media-behind-post** — md5 the uploaded/CDN media against the local `.mp4`.
- **Human eye** — Brent's job; flag which pieces still await his eyes.

## Step 5 — LOG + report

- **Record the term as burned, immediately after a successful ship:**
  ```bash
  ~/Desktop/The\ Brag-Machine/machine/scripts/burned.sh add "<term>" "<YYYY-MM-DD>"
  ```
  If that command exits 1 it means the term was ALREADY burned and should never have
  shipped — do not suppress it, report it to Brent as a defect in this run.
- Append each shipped piece (surface, slot, caption first-line, media md5, post id)
  to the run report with a **UTC** timestamp.
- Report: what was already covered, what shipped, new runway, and anything
  UNVERIFIED. **Prove-it discipline:** command + output + UTC, or say `UNVERIFIED`.
- **Per shipped piece, state WHICH verification levels passed, each with UTC** —
  API status · media-behind-post md5 · human-eye (Brent's, so name it as still
  owed if he hasn't watched it). **Never report a bare "posted."** A piece with
  any level unconfirmed is reported UNVERIFIED, not shipped.
- **NEVER echo the Blotato API key.**

## Weekly (Sun→Sat)

Pull unique views per piece/surface so reach can be correlated to **BUYERS** (the
metric that matters — not eyes, not leads). If no views source is wired yet, say so
plainly (UNVERIFIED, name the missing dependency) — the checker's `WTH-VIEWS` row
tracks the same gap.
