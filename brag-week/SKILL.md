---
name: brag-week
description: Batch day - produce and schedule a full week of content on the Brag Machine in one sitting. Use when Brent says "we need a week of content", "do a batch", "batch day", "load next week". Renders the week's briefs, stages a numbered review folder, and on Brent's approval-by-number schedules everything into the 30-day-plan calendar slots (EN + Thai).
---

# brag-week — a week of content in one sitting

Sources: `~/Desktop/POSTING-PLAN-30-DAYS.md` (the calendar) · `~/Desktop/JOURNEY-PRODUCTION-QUEUE.md` (ready briefs) · `machine/SOTU.md` (state) · `machine/cadence/` (ramp + no-repeat ledger).

## The loop

1. **Pick the week** from the calendar (next unfilled slots). Typical week = 3 Agent Laws + 2 Journey episodes + 1 tile (+ Sunday YouTube handled by the YT system).
2. **Render the batch** — one background bash chaining the `./claw` briefs sequentially (each is one brain run; ~3 min/video). All `--dry`.
3. **Auto-fix note:** claw self-heals hard-kill/font gate errors. A residual LOUD FAIL = real design problem — fix the composition in place, `npx hyperframes check && render` (never re-pay the brain).
4. **Music check:** journey/coaching/motivational must carry `journey-theme.mp3` (auto via styles; verify on spot-checks).
5. **Voice pass:** AGENT LAWS get Brent VO via `scripts/vo.sh` (see brag-voice skill). Journey eps stay silent (style law). VO runs are single-lane — do them sequentially after renders.
6. **Thai pass:** every Journey episode gets a Thai version (see brag-one skill's Thai section — copy composition, translate with .th class + Thonburi + syllable-chunk typing, render free).
7. **Stage review:** `~/Desktop/BATCH-WEEK<N>/` with numbered descriptive names (`1-LAW5-one-step.mp4`...). Unique filenames ALWAYS (QuickTime shows stale windows on reused names). `open` folder + first video.
8. **Brent approves by number** ("all good" / "all but 4"). Fix rejects in place.
9. **Schedule approved** via adapter (no re-render): weekday slots 16:00Z (9AM Phoenix), Thai slots 01:00Z next-day (8AM Thailand, facebook+tiktok), tiles Saturday (x,instagram,facebook). Blotato rate-limits ~30 posts/min — on a LOUD FAIL late in a run, sleep 10 and retry just the missed channel.
10. **Ledger:** append every scheduled batch to `machine/ledger.jsonl`. Log used ideas to `machine/cadence/cadence-state.json` (no-repeat law).
11. **Update SOTU** if state changed; append the delta to `machine/HANDOFF.md` for other instances.

## Type-size law (mobile legibility — Brent 2026-07-23)
Every style file carries minimum type sizes; the key statement is >=64px on the 1080 canvas, nothing load-bearing below 54px. Verify on spot-checks — small text that looked fine in QuickTime is unreadable in a feed.

## Costs

Brain runs = credits (one per new video). VO, Thai, stitches, re-renders, fixes, scheduling = free. When credits are tight: template/stitch/re-skin lanes only.
