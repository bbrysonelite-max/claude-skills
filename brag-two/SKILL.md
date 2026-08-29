---
name: brag-two
description: Chain TWO or more rendered Brag Machine videos into one longer film (pin them together) and optionally queue it - compilations, week recaps, YouTube cuts from Shorts. Use when Brent says "pin these together", "stitch", "make a longer one from those", "compilation", "season cut". Free - no brain run, pure ffmpeg. For a single new video use brag-one.
---

# brag-two — pin renders into one film

Machine: CHEESEGRATER's live clone — `cd ~/Desktop/The\ Brag-Machine/machine && git pull` (state: `SOTU.md`; history of every render: `ledger.jsonl` + `runs/`). The iMac's copies are stale remnants — never run them; the two Desktops do NOT sync (grounded 2026-08-25).

## The move

```bash
./claw --stitch <runId1>,<runId2>[,...] [--channels ...] [--at ISO] [--cta url] [--dry]
```

- Run IDs are `runs/` folder names (find them in `ledger.jsonl` — it records every video with its prompt).
- **Same format only** (all vertical or all landscape) — the guard LOUD-FAILs on mismatch by design.
- Caption: first run's caption by default; pass new text as the prompt to override. `--cta` appends the link if absent.
- Output lands in a new `runs/<ts>/` with its own ledger line.

## Patterns

- **Longer reel:** 2 episodes pinned ≈ 50s vertical — good for "story so far" posts.
- **YouTube cut:** stitch the week's landscape renders; per the 30-day plan, Sunday compilations (e.g., Journey EPs 1-5) go to the YouTube system with a Two Brents clone intro/outro. Two-channel law (2026-08-25): longform/compilations = main @BrentBrysonaios channel, MANUAL upload only (never Blotato); WTH/volume shorts = the "What the Freakin' Hell is Ai" channel via Blotato account 47853, private-first.
- **Re-render nothing:** if a piece only exists vertical and you need landscape for the cut, that's a new render decision — flag the cost to Brent first.

## Queue

Dry by default for review (`open` the output with a unique Desktop filename). On approval: adapter direct — `./adapters/blotato.sh <out.mp4> <caption.txt> <channels> "<at>" draft` — and append to `ledger.jsonl`.
