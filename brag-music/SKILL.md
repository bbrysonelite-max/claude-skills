---
name: brag-music
description: Source, audition, and lock music for Brag Machine video series - licensed catalog tracks resolved as candidates Brent picks by ear. Use when Brent wants new/better/less generic music, a theme for a series, or says "find music", "the music is generic", "new theme". Never use commercial songs or covers (melody is copyrighted even instrumental - Content ID mutes/claims). Locked themes live in the machine's template assets and style files.
---

# brag-music — series themes, licensed, picked by ear

## Resolve candidates (licensed catalog, free)

```bash
export PATH="/usr/local/opt/node@22/bin:$PATH"
node ~/.claude/skills/media-use/scripts/resolve.mjs --type bgm \
  --intent "<mood in plain words: genre, energy, tempo, what it's for>" \
  --project ~/Desktop/The\ Brag-Machine/machine
```

- Pull 2-3 per round with DIFFERENT mood phrasings; files land in `machine/.media/audio/bgm/`.
- Copy each to `~/Desktop/<series>-theme-<letter>-<hint>.wav` and `open` the first — Brent auditions by ear and answers with a letter. "That was close" = keep direction, pull tighter variants. Iterate rounds until a pick; rounds are free.

## Lock a pick (this is what makes it a THEME)

1. `ffmpeg -i <pick>.wav -c:a libmp3lame -b:a 192k machine/templates/tigerclaw-launch/composition/assets/music/<series>-theme.mp3` (template assets are staged into every run).
2. Write it into the style file's Audio section (`machine/style/<style>.md`) as LOCKED with Brent's date — name volumes, fades, and that substituting stock is forbidden.
3. Commit + push the mp3 and style law to the brag-machine repo.
4. Swap into any existing renders free: copy mp3 into run assets, sed the `<audio src>`, re-render.

## Standing decisions (2026-07-23)

- **journey-theme.mp3** (rock stomp) = THE Brent sound: journey + coaching + motivational styles all carry it. Happy-beats stock stays ONLY for Tiger product / business-promo.
- Commercial songs and their covers are never used - the SWAGGER gets matched, not the melody ("Long Way to the Top" rule).
- Original generated anthems: ElevenLabs music once Brent's key lands (Higgsfield connector is speech-only - no standalone music).
