---
name: brag-machine
description: "Use when Brent wants ANY video made or posted by the machine — motivational quote videos, coaching/teaching videos, a promo for any business or website, positive/personal/feel-good videos, chaining past videos together — or says \"run the machine\", \"make a video about X\", \"post a video\", \"claw it\". Siblings: /brag-one for one video end-to-end (Thai + voiceover), /brag-two to stitch renders into longer films, /brag-music to lock series themes, /wth-campaign to ship already-reviewed stock. NOT for editing footage or captioning existing video — use the hyperframes skills."
---

# The Brag Machine — Operator Skill

One command turns a prompt into a rendered, gated, queued video. **Read `machine/SOTU.md` FIRST in
any fresh session — it is the current-state map.** The machine is the SOCIAL system; longform is the
separate YOUTUBE system (Two Brents, `~/Desktop/YOUTUBE`) — never mix them.

```bash
# Run on CHEESEGRATER (192.168.0.2) from the LIVE clone — git pull first:
cd ~/Desktop/The\ Brag-Machine/machine && git pull
./claw "VIDEO REQUEST" [flags]
```

**Render target (grounded 2026-08-25):** canonical repo is private
`github.com/bbrysonelite-max/brag-machine`; the live working clone is **cheesegrater's**
`~/Desktop/The Brag-Machine/machine` (a real git clone, verified on commit 1294d63). The iMac is NOT
a render target — its own `~/Desktop/The Brag-Machine`, Dropbox `Browser-Claude`, and iCloud
`Share Folder` copies are stale remnants; never run those. The two machines' Desktops do NOT sync.

**Brand law:** Tiger-brand renders obey the `tigerclaw-primitives` repo
(`github.com/bbrysonelite-max/tigerclaw-primitives`, local clone `~/tigerclaw-primitives`; git pull
first) — real tokens + logo files, never hand-approximated. Personal-brand styles
(journey/coaching/motivational) have their own locked look and are exempt.

**Absorbed engines (2026-07-23):** `machine/voice/` = Brent's text voice (6 named cadences,
never-say compliance, gold examples — use for ALL captions/posts) · `machine/cadence/` = posting
calendar machinery (volume ramp, warm-up, no-repeat usedIdeas ledger in cadence-state.json) ·
`machine/docs/blotato-rest.md` = REST gotchas.

## Route the subject to a style

| Brent asks for | Flag | Notes |
|---|---|---|
| Tiger Claw / product content | (none — HOUSE-STYLE default) | locked brand |
| Motivational quote | `--style motivational` | one quote, huge type, vertical default |
| Coaching / teach one thing | `--style coaching` | pain → shift → numbered steps |
| Business / website promo | `--style business-promo` | put the business's name, URL, real copy, brand color IN the prompt; always `--cta <url>` |
| Positive / gratitude / personal | `--style positive-post` | gentle motion; personal ones are ALWAYS `--dry`, never queued |

## Flags

- `--format landscape|vertical|square` (default landscape; vertical for TikTok/Reels/Shorts/phone)
- `--channels x,instagram,tiktok,facebook,linkedin[,youtube]` — **YouTube law (2026-08-25):** youtube is NEVER a default and NEVER goes in DEFAULT_CHANNELS (adapter hard-fails). It posts ONLY to the WTH volume channel "What the Freakin' Hell is Ai" (Blotato account 47853), private-first, explicit per-run only — and only once brag-machine PR #24 is merged (until then the adapter on main still blanket-denies youtube). The main @BrentBrysonaios channel is disconnected from Blotato: manual uploads only, forever.
- `--cta <url>` — end-card link + auto-appended to caption (clickable links live in captions, never in the MP4)
- `--dry` — render only, no posting · `--draft-quality` — fast iteration render
- `--at "ISO-UTC"` — schedule; without it, draft mode schedules **+6h** (Blotato has no true drafts — delete in dashboard to cancel)
- `--stitch run1,run2,...` — chain past runs (`machine/runs/`) into one film; free, no brain; formats must match
- `--template tigerclaw-launch` — reuse proven video, zero tokens

## Laws of operation

1. **Brain runs cost Claude credits** (claw calls `claude -p`); template and stitch runs are free. Say which you're doing.
2. **Personal videos** (family, private notes) are always `--dry` and never queued to channels.
3. **Queue as draft by default.** `--live` only when Brent explicitly says so.
4. **Rich prompt beats flags:** the VIDEO REQUEST carries the brief — audience, copy, brand color, URL, end-card. For business promos, prompt-inject the business's REAL copy; never invent claims.
5. **After a render, open the video** (`open runs/<ts>/out.mp4`) so Brent approves before anything is queued. To queue an approved dry render without re-paying the brain: `./adapters/blotato.sh <out.mp4> <caption.txt> <channels> "" draft`.
6. Every run logs to `ledger.jsonl`; past runs in `runs/` are the b-roll/stitch library.
7. Node: the machine pins Node 22 via `machine.env` — don't "fix" node versions globally.
8. Secrets: load `BLOTATO_API_KEY` by name via **/loading-secrets** — that skill holds the canonical path per machine and the read discipline. Never echo it. **Gotcha (2026-08-25):** the key contains `+`/`/`/`=`, so never extract it with a `[A-Za-z0-9_-]` regex — it silently truncates.
9. **Receipt:** report the run dir, the `out.mp4` path, brain-vs-template/stitch, and per channel the post id + scheduled UTC — or the word UNVERIFIED. Never a bare "posted."

## Wow features to reach for

- On-screen URL end-card + caption link (`--cta`) to funnel into the backend/mailing list
- Stitch a themed compilation from past runs (`--stitch`)
- The brain has the full HyperFrames skill suite installed (motion-doctrine, cut-the-curve, seam-craft…) — ask for cinematic moves in the prompt ("zoom-through seam", "waterfall entry", "stat count-up") and it will execute them.
- New subject = new file in `style/` copying an existing one's structure; commit + push when adding one.
