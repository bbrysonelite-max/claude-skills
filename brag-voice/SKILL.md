---
name: brag-voice
description: Brent's voice for any video or audio - local Voicebox clone (his ruling - "best generated voice I have ever had"). Use when adding narration/voiceover to a render, making a talking version of a video, generating Brent speech from text, or when Brent says "put my voice on it", "narrate it", "make it talk". Free, local, unlimited. HeyGen is for ON-CAMERA avatars only (separate YouTube system); this skill is voice-only.
---

# brag-voice — Brent's voice, locally, free

**The voice:** Voicebox app (jamiepine/voicebox) on this Mac, API `http://127.0.0.1:17493`. Profile **"Brent Bryson"** `18836009-0527-4b9f-9837-3d58c2a0dc76` — cloned from his own footage, approved with chills.

## The one-command lane (narrate a render)

```bash
cd ~/Desktop/The\ Brag-Machine/machine
./scripts/vo.sh runs/<run-id> "<narration text>" [delay-ms]   # → runs/<run-id>/out-vo.mp4
```
Generates the speech in Brent's voice, ducks the music to 0.35, mixes, never re-renders video. Copy result to Desktop under a UNIQUE name and `open` for his review.

## Raw speech (no video)

```bash
curl -s -X POST http://127.0.0.1:17493/generate -H "Content-Type: application/json" \
  -d '{"text":"...","profile_id":"18836009-0527-4b9f-9837-3d58c2a0dc76","language":"en"}'   # returns {id}
# poll: curl -s "http://127.0.0.1:17493/history?limit=10" | jq '.items[] | select(.id=="<id>") | .status'
# fetch: curl -s "http://127.0.0.1:17493/audio/<id>" -o out.wav
```

## Gotchas (all hit and solved 2026-07-23 — do not rediscover)

- App must be running: `open -a Voicebox`; wait for API 200 on /profiles.
- `/history` wraps results in `.items[]`. `/generate/{id}/status` is an SSE stream — do NOT curl it with a timeout and parse as JSON; poll /history.
- Server is single-lane: wait for no `generating`/`loading_model` items before POSTing (vo.sh does this).
- "librosa stub" error = stale server bundle → quit + relaunch the app.
- New voice samples: max 30s audio + exact `reference_text` transcript (transcribe with `npx hyperframes transcribe`; its JSON is an ARRAY of {start,end,text}).
- **VOICE DRIFT (2026-07-23, Chrissy video):** ellipses/long pauses in the text can make the clone DRIFT to a different voice (even female) mid-read. Write continuous natural sentences — no "...", no stage pauses. If drift happens anyway, regenerate (seed varies). Human ears verify every personal/shipping VO.
- First generation after app start loads Qwen 1.7B — slow on this Intel Mac; later ones are fine. Batch VO accordingly.
- Voicebox MCP is registered for the machine project (`claude mcp` → voicebox).

## Timing law (Brent, 2026-07-23 — refined over Law #5 v1–v3)

- **Don't cut the words to fix timing** — the script's natural length is usually right (Brent: "it says exactly the right amount"). Fix ENTRY and PACING first.
- **Start with a real gap:** ~2000ms after video start (never <1500ms) — the hook lands, THEN the voice comes in.
- **Hard ceiling only:** narration must end ≥1.5s before the video ends — vo.sh enforces and prints a word budget ((video−delay−1.5)×2.3). That budget is the CEILING for trimming, not a target.
- **Sync watch-out:** if the voice describes something 10s after it left the screen, the fix is usually the composition's scene holds (or splitting the narration to land per-scene), not shorter text.
- Voice v1 of any new format gets Brent's ears before it ships.

## Format rulings (Brent)

- **AGENT LAWS ship with his voice.** JOURNEY episodes stay text-films (style law) — narrated versions are a YouTube/compilation flavor, not the Shorts default.
- English VO = Voicebox. Thai-in-Brent's-voice = ElevenLabs multilingual (1.5M credits parked) if/when wanted — key must arrive via file in ~/Desktop/GitSync/ (the consolidated credentials file), never chat.
- Personal/family videos never get queued anywhere, voiced or not.
