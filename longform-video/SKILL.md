---
name: longform-video
description: Build a longform YouTube video for @BrentBrysonaios in the PROVEN mixed format — Brent's real on-camera footage interleaved with faceless HyperFrames teaching beats (Voicebox VO), optional blue-shirt clone appearances, and the LOCKED uniform cards from Youtube-system. Use for "make the video", "longform", "episode", "rework this cut". Shorts are cut FROM the output afterward (never sourced elsewhere). Proven end-to-end 2026-08-29 on what-is-a-flavored-agent-v5.mp4 (289.6s).
---

# longform-video — the mixed-format longform line

Proven 2026-08-29 (v5, 4:50, exit=0). Every rule below was paid for that night or earlier.
Read `/two-brents-brand` FIRST for voice/story/compliance. This skill is the PRODUCTION layer.

## The format (locked by Brent 08-29)

1. **Picture** = three interleaved sources:
   - Brent's REAL footage (hook, teaching-on-camera, ground/CTA, demo) — never re-cut mid-take without transcript timings.
   - **Faceless HyperFrames beats** for AI-Brent teaching (via `/faceless-explainer`) — Broadside-class ink/brass kinetic type. Brent 08-29: "I love what you did with the graphics."
   - **Blue-shirt clone appearance** (HeyGen registry `ai_brent` 44f56d7e) in 1–2 banter beats so viewers SEE who's talking — "nobody knows what the hell is going on, it's just my voice." Not every beat. Existing rendered modules first; NEW HeyGen render = ping Brent the dollar amount BEFORE spending, free `test:true` + his eyeball before credits (registry law).
2. **Voice** = Brent's Voicebox clone (profile `18836009-0527-4b9f-9837-3d58c2a0dc76`, `/brag-voice`) for all faceless narration. Clone modules carry their own HeyGen ElevenLabs voice — acceptable per Brent 08-29, keep appearances short.
3. **Cards — LOCKED, from Youtube-system** (`~/Desktop/YOUTUBE/hyperframes-cards/`, repo `bbrysonelite-max/Youtube-system`; read `CARDS-LOCKED.md` before trusting any render):
   - FRONT `intro/frontcard-uniform.mp4` (5s) — the follow/"keep the lights on" ask. Place after the hook, or at the first clean cut near the 90-second mark.
   - BACK newest `endcard/endcard-v*.mp4` (14s) — SUBSCRIBE + type-CLAW + brentbryson.ai SPELLED OUT. Never ship a homemade "link below" card: **every CTA card must show a typed URL or word people can spell.**
   - `tap-card/tap.mp4` — CLAW conversion, optional mid-video.
   - Stale-render trap: after editing a card source, re-render AND look at a frame.
4. **Compliance** — `python3 ~/Desktop/YOUTUBE/scripts/compliance_check.py <every text>` before render. No company name near any dollar figure, ever, on-canvas included ($25M stands alone). Public fence words apply.

## Pipeline (each gate has a receipt or you stop)

1. **Script gate** — Brent-approved script, verbatim (VO_MODE verbatim). No script, no build.
2. **VO** — generate/reuse Voicebox wavs per AI beat. `ffprobe` every wav; faceless frame duration = wav + 0.4–0.6s pad.
3. **Faceless project** — `/faceless-explainer` INSIDE the video's system folder (`videos/<project>/`), one folder per system. Mark SILENT (`music: none`, no SCRIPT.md) — pipeline TTS default is a stranger's voice; never let it generate narration. One Opus worker per frame, packets via frame-packets.mjs. Fonts: pin identical `@font-face` gstatic woff2 blocks in EVERY frame (workers diverge — normalize before lint) + vendor woff2 into `assets/fonts/`.
4. **Checks to zero** — `npx hyperframes lint` + `check` = 0 errors. Known traps: letterSpacing/layout-prop tweens (stutter — transforms only), multi-writer GSAP tweens on one property (seek renders camera frozen — ONE driver tween per property), `#root .clip` specificity overriding positioned `.clip` elements, exits at clip boundaries need `tl.set` hard kill. Overlap errors: mark `data-layout-allow-overlap` ONLY after looking at the frame.
5. **Render** — `npx hyperframes render --quality high` (local, $0). Snapshot contact sheet, LOOK at it.
6. **Assembly** — script file, never inline (rtk mangles ffmpeg vars; bash `$((...))` treats "09" as bad octal — no numeric-string array keys). Re-encode EVERYTHING to one spec before concat: `1920x1080, 30fps, libx264 crf19, aac 192k 48k stereo`; upscale 720p cards with scale+pad; add anullsrc silence to soundless cards; mux VO with `-map 0:v -map 1:a -af apad -shortest`. Concat with `-c copy` over the list file.
7. **QC (real eyes)** — pull frames at faceless, real-footage, clone, and card offsets; `volumedetect` at VO and footage spots (expect ≈ -20 to -30dB mean, same ballpark both). Compute offsets from per-segment ffprobe durations, never from memory.
8. **Chapters + metadata** — re-measure chapter marks from actual segment durations every re-cut; description carries the C1 canonical block.
9. **Brent gate** — he watches the file. NEVER upload; upload is his. Rung 4 until his eyes = rung 5.

## Hard laws inherited
- No music bed decision inside faceless renders; bed (if any) at final assembly.
- Shorts = cut from THIS longform only.
- ffmpeg build here has NO drawtext; cards via PIL or HyperFrames.
- Whisper lane = brew `whisper-cli` + ggml-base.en.bin (Voicebox /transcribe is broken).
- Deliver ONE file per iteration (v1, v2 …), keep prior versions, never overwrite his kept cut.
