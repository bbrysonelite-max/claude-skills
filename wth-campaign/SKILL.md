---
name: wth-campaign
description: Use when Brent or Jill's schedule says "run the WTH campaign", "fill the WTH queue", "wth daily", "refill the social queue", on the daily WTH tick, or any time the WTH social queue is reported short, out of band, or its stock is questioned. Also use before scheduling anything to the 6 locked WTH surfaces. This skill only SHIPS already-reviewed stock — to render or make new video use /brag-machine instead. It is not the checker; the WTH-* rows in ~/daily-checks/run.sh grade this work independently.
---

# WTH Campaign — the daily DO-ER (Jill)

You are the **DOER**, not the checker: ground the live queue, decide if it is short, and if so refill
from **CORRECT** stock and ship up to the ceiling. Never grade yourself against your own log — the
`WTH-*` rows in `~/daily-checks/run.sh` query Blotato themselves and grade this run mechanically.

Field-level Blotato how-to: `references/mechanics.md` (load it before grounding or shipping).
Full locked spec: `~/Desktop/WORKROOM/SOCIAL-ONE-TASK-SPEC-LOCKED.md`.
Canonical loop + traps: `~/Desktop/The Brag-Machine/machine/RUNBOOK.md`.

## The rules this holds (Brent, LOCKED 2026-08-24)

- **Cadence:** 3 UNIQUE pieces/day, 7 days/week, each fanned to ALL 6 locked surfaces.
- **Queue band:** never **< 7 days** remaining (that floor is the refill alarm), never **> 15 days**
  out (the ceiling — stop building).
- **6 LOCKED surfaces:** Facebook · Instagram · LinkedIn · TikTok · X @brentbryson ·
  X @pebobryson801. **The main YouTube channel (@BrentBrysonaios / Two Brents) is EXCLUDED FOREVER**
  — never post the campaign there (that crossing cost ~1,000 views/week; it is disconnected from
  Blotato entirely). **Note 2026-08-25:** the dedicated WTH volume channel "What the Freakin' Hell is
  Ai" (Blotato account 47853, private-first) is NOT one of this skill's locked surfaces — do not add
  it to the daily fan until Brent locks a new surface spec that includes it.
- **8-week window:** 2026-08-23 → 2026-10-23, reviewed weekly (Sun→Sat).
- **Terminology:** a piece is either **CORRECT** (cleared the 7-point Quality Bar) or a **draft**.
  No "blessed", "approved", or "blast" — say CORRECT.

## BOUNDED AUTONOMY — the hard law

- Ship **ONLY** stock listed CORRECT in `~/Desktop/WTH-CAMPAIGN/CORRECT-STANDARD.md`. Sitting in a
  stock folder is NOT proof; the manifest is. Anything it does not cover has unknown provenance →
  **UNVERIFIED: hold it, flag Brent, never ship it.**
- **NEVER** render, generate, rewrite, or improvise new/unreviewed content. New content needs Brent.
- Ship only to the 6 locked surfaces, only on cadence, only up to the 15-day ceiling.
- **Stock empty (or too thin to reach 7 days) = STOP and LOUD-ALARM Brent.** Do not fabricate, do not
  silently render, do not stretch by re-posting dupes.
- **"Rendered" ≠ CORRECT. "Looks done" ≠ done.** Quality Bar — RUNBOOK "THE QUALITY BAR" + "STANDING
  LAW — never hand Brent unchecked work product" (Brent, 2026-08-24): read them, do not paraphrase
  them away. All seven must be true and checked: 1. reads like Brent (cadence on the payoff,
  compliance holds) · 2. brand on (only `tokens.json` hex, brand book applied) · 3. structure sound ·
  4. **SOUND ON** (VO at/above the coverage floor) · 5. CLAW mark on screen at t=0 · 6. nothing
  overflows · 7. captions right, nothing clipped, it actually plays. Any check unconfirmed →
  **UNVERIFIED, STOP, do not post, alarm Brent.** What reaches Brent is watchable proof, not
  something he has to inspect for defects.

## Tools (only these)

1. **Blotato MCP** (wired into hermes, 35 tools) — the ONLY posting path. Adapters / raw-curl retired.
2. **`CORRECT-STANDARD.md`** — the ship gate; read it every run. Currently lists the
   `WTH-CLAW-READY/*.mp4` cards and the `er-01/shorts/*.mp4` ER networker reels — the same gated
   pipeline as the human-eye-verified Aug 18-21 posts, the reference for what CORRECT looks like.
3. **Ready stock:** `~/Desktop/WTH-CAMPAIGN/WTH-CLAW-READY/` (`WTH-*-CLAW-v1.mp4`) ·
   `~/Desktop/The Brag-Machine/machine/longform/er-01/shorts/`
4. **Burned-terms registry** — dedup source #2 alongside the live queue captions. Commands + history
   in `references/mechanics.md`.

## Step 1 — GROUND the queue LIVE (always first)

Cached counts rot. Read Blotato now and count **UNIQUE first-line captions per day, NOT rows** — one
piece fans to 6 rows, so counting rows makes a 1-piece day read as 6 (RUNBOOK §1 trap 3). Compute
runway, per-day unique pieces, and surface fan. Exact fields: `references/mechanics.md`.

## Step 2 — DECIDE

- Runway ≥ 7 AND coming days at 3 unique × 6 surfaces → **nothing to do. Say so and stop.**
- Runway < 7 OR an upcoming day short → **REFILL.** Runway > 15 → **stop building.**

## Step 3 — REFILL + SHIP (only when short)

1. **HARD GATE, run for EVERY candidate before it is scheduled:** `burned.sh check "<term>"` —
   exit 0 safe, **exit 1 = ALREADY PUBLISHED, do NOT ship it, pick another.** Never override, never
   "ship it anyway", never edit the registry to make a candidate pass. Every remaining candidate
   burned = stock exhaustion → loud-alarm Brent and stop. **A repeat post is worse than a missed slot.**
2. Gate every survivor against `CORRECT-STANDARD.md`. Only CORRECT stock proceeds.
3. Ship per surface at the 16:00 / 19:00 / 22:00Z slots, filling forward only up to today+15, with
   the per-surface caption formats — all in `references/mechanics.md`.
4. Stop when runway reaches the band (aim for the ceiling), or on stock-out → loud-alarm and stop.

## Step 4 — VERIFY (3 levels; "verified" without the level is a lie)

**API status** · **media-behind-post md5** · **human eye** (Brent's — name which pieces still await him).

## Step 5 — LOG + report

- Record the term burned immediately after a successful ship (`burned.sh add`). If that exits 1 the
  term was ALREADY burned and should never have shipped — do not suppress it; report it to Brent as a
  defect in this run.
- **Receipt format:** per shipped piece — surface, slot, caption first line, media md5, post id, and
  WHICH verify levels passed, each with UTC. Command + output + UTC, or the word `UNVERIFIED`. Never
  report a bare "posted."
- **NEVER echo the Blotato API key** — load it by name via /loading-secrets.
- End state: what was covered, what shipped, new runway, anything UNVERIFIED — or one
  decision-ready question for Brent.

## Weekly (Sun→Sat)

Pull unique views per piece/surface so reach can be correlated to **BUYERS** (the metric that matters
— not eyes, not leads). No views source wired yet → say so plainly (UNVERIFIED, name the missing
dependency); the checker's `WTH-VIEWS` row tracks the same gap.
