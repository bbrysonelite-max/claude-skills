---
name: brag-personal
description: Personal message videos - THE MACHINE personalized for one recipient with Brent's voice carrying his exact words. Use when Brent says "make one for <name>", "send a personal video", "do one like Chrissy's/Becca's", or gives a quoted message for a specific person. HIGH-VALUE lane (Brent - "a million uses"). NEVER queued to social - gift files only.
---

# brag-personal — one person, Brent's words, his voice

Proven prototypes: Becca (positive-post style) · Chrissy (personalized THE MACHINE). Fast path: clone a proven composition, personalize, voice, mix.

## Brent's order format (parse exactly)

1. **WHO** — recipient FIRST NAME only (Brent's law 2026-07-23: personal videos use first names everywhere — screen and voice; warmer, and kills the surname-spelling risk). Relationship for context. **NAME-SPELLING LAW (Brent, 2026-07-23): never render a name without confirming the exact spelling first** — dictation mangles names (Mac/Mack, Chrissy). One quick question before the build: "spell the name for me?" Applies to on-screen text; the voice only says the spoken form.
2. **QUOTED MESSAGE** — text in quotes is spoken VERBATIM. Nothing outside quotes is ever voiced. If unclear what's quote vs context, ask ONE question before generating.
3. **SIGNATURE** — on-screen ONLY (e.g. "— Uncle Brent"). The voice NEVER reads the signature (law, 2026-07-23: "that was meant to be a signature").
4. Optional **VALUE BEAT** — a quick tip/thought to include as its own scene.

## Build lane

1. Clone base: a past run's `composition/` from the brag-machine repo's `runs/` history (fresh clone of `github.com/bbrysonelite-max/brag-machine` — THE MACHINE reveal, personalized like Chrissy's) or a `positive-post` render (gentle, like Becca's). Personalize: name in hook, `$ ./claw "for <Name>"` terminal line, message lines as cards, on-screen signature, closing wink line.
2. `npx hyperframes check` → render silent.mp4 (free).
3. VO via Voicebox profile 18836009-0527-4b9f-9837-3d58c2a0dc76 (see brag-voice skill): one intro line + the quoted message, CONTINUOUS sentences, no ellipses, no signature. Delay ~1500ms; timing law applies.
4. Mix: ffmpeg duck-mix (music 0.35, vo 1.5, `-movflags +faststart`).
5. **Verify playable** (ffprobe duration) BEFORE delivering. Fresh unique filename every version (`for-<name>-FINAL.mp4`) — NEVER overwrite a file QuickTime may have open.
6. Deliver to Desktop + `open`. Brent's ears approve; voice-drift = regenerate.

## Laws

- **Rules are forward-looking.** When Brent amends a rule, apply it to the NEXT video. Never redo a sent/approved video unless he explicitly asks — redos are the expensive part (ticket #10).

- NEVER queue personal videos to any channel. They are gifts Brent sends himself.
- Voice reads only quoted words + intro. Signature on screen only.
- Iterate free: text swaps + re-render cost nothing; only his words are sacred.

## Color convention (Brent, 2026-07-25)

Colors are dialed by what Brent SAYS in the order — nothing else:

1. **Says nothing** → DEFAULT palette (personal warm: cream `#F2EADD` on `#0B0A08`, accent `#FF6B1A`) — the hardcoded look Pat/Chrisie got.
2. **"Use the brand colors"** → primitives tokens.json: `#0A0A0A` bg · `#f5f5f5` ink · `#E8722A` accent · `#4ADE80` signal green (payoff lines only).
3. **Any mood/color words** ("soft", "navy and gold", "her favorite color is purple") → agent mixes a custom palette from those words.
4. **"Your call" / "go wild"** → agent has full creative license — and MUST USE IT (ticket #15): push PAST comfortable. Unexpected palette, dramatic motion, at least one choice that surprises. Tasteful-default = failing the instruction.

Rails that always hold: `hyperframes check` contrast gate (WCAG AA) must pass; tone matches the message (sympathy never gets neon); Brent's eyes are the final gate before he sends — a rejected palette costs one free re-render.

Mechanics: clone base `templates/brag-personal/composition/` — ALL colors are CSS variables in one `:root` block at the top (default + brand values listed in the comment beside it). Swap the block, never hunt scattered hex codes. Glow/gradient rgba tints derive from `--accent` — swap together.
