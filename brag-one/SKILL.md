---
name: brag-one
description: Render ONE video end-to-end on the Brag Machine - brief → styled render → review → queue. Use when Brent says "render one", "make a video about X", "do Agent Law N", "do Journey EP N", or wants a single social video produced and posted. Handles the full lane - English render, optional Thai localization, optional voiceover mix, queue to channels. For chaining videos use brag-two; for system state read machine/SOTU.md first.
---

# brag-one — one video, end to end

Machine: CHEESEGRATER's live clone — `cd ~/Desktop/The\ Brag-Machine/machine && git pull` (read `SOTU.md` first in a fresh session). The iMac's copies are stale remnants — never run them; the two Desktops do NOT sync (grounded 2026-08-25).

## The lane

1. **Brief.** Pull the ready brief from `~/Desktop/JOURNEY-PRODUCTION-QUEUE.md` if it exists there; else write one: hook in first 2s, one idea, verbatim quotes where applicable, CTA. Route style: journey (doc episode) / coaching (Agent Law) / motivational (quote) / positive-post (personal) / business-promo (any business) / default (Tiger product).
2. **Render dry.** `./claw "<brief>" --style <s> --format vertical --cta <url> --dry` (background it; brain run costs credits — one per video).
3. **Gate fails?** Fix the composition IN PLACE (common: missing `tl.set(...,{autoAlpha:0},boundary)` hard kills; undeclared fonts — mono must be `Menlo, monospace`), then `npx hyperframes check && npx hyperframes render --quality high --output ../out.mp4` in the run dir. Never pay a second brain run for gate errors.
4. **Music check.** Journey/coaching/motivational MUST carry `assets/music/journey-theme.mp3` (the locked stomp). If the composition references happy-beats, swap: copy theme into run assets, sed the src, re-render (free).
5. **Review.** Copy to `~/Desktop/<unique-name>.mp4` (unique name — QuickTime shows stale windows under reused names) and `open` it. Brent approves before any queue.
6. **Queue (no re-render):** `./adapters/blotato.sh <out.mp4> <caption.txt> <channels> "<ISO-time-or-empty>" draft`. Slots: EN 16:00Z (9AM Phoenix), TH 01:00Z next day (8AM Thailand). Append a line to `ledger.jsonl`.

## Thai pass (when the piece ships bilingual — Journey always does)

Copy the run's composition to a new run dir, then: add `@font-face {font-family:"Thonburi"; src: local("Thonburi");}`; put Thonburi first in body font stack; add `.th { letter-spacing:0!important; line-height:1.35!important; }` to every translated element; translate text (keep date chips/file receipts/series lockups in English); typing effects reveal WHOLE Thai syllable chunks per `<i>`, never per character (combining vowels detach); write Thai caption.txt; check + render (free). Queue to facebook,tiktok for the Thailand-morning slot.

## Voiceover (English lane — see brag-voice skill)

- **Brent's voice = local Voicebox clone** (his ruling: the best he's had). One command: `./scripts/vo.sh <run-dir> "<text>" [delay-ms]` → `out-vo.mp4`. AGENT LAWS ship voiced; Journey eps stay text-films.
- Fallback stand-in only if Voicebox is down: `npx hyperframes tts --voice am_michael` + the ffmpeg duck-mix (same filter vo.sh uses).

## Type-size law (mobile legibility — Brent 2026-07-23)
Every style file carries minimum type sizes; the key statement is >=64px on the 1080 canvas, nothing load-bearing below 54px. Verify on spot-checks — small text that looked fine in QuickTime is unreadable in a feed.

## Laws

Draft-by-default (+6h) unless `--at`; personal videos NEVER queue; captions in Brent's voice (cadence bank: `machine/voice/voice.md`, compliance: `machine/voice/never-say.md`); no company names from his past industry; log every idea used to `machine/cadence/cadence-state.json` usedIdeas (no-repeat law); update `machine/SOTU.md` if state changed.
