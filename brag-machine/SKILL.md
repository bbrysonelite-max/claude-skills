---
name: brag-machine
description: Drive the Brag Machine (claw) — turn a prompt into a branded, beat-synced video and queue it to social. Use when Brent wants ANY video posted or made by the machine - motivational quote videos, coaching/teaching videos, a promo for any business or website, positive/personal/feel-good videos, chaining past videos together, or "run the machine / make a video about X / post a video". Routes subject → style. NOT for editing footage or captioning existing video (use hyperframes skills).
---

# The Brag Machine — Operator Skill

**Read `machine/SOTU.md` FIRST in any fresh session — it is the current-state map.** Companion skills: `brag-one` (one video end-to-end incl. Thai + voiceover), `brag-two` (stitch renders into longer films), `brag-music` (source + lock series themes). The machine is the SOCIAL system; longform is the separate YOUTUBE system (Two Brents, ~/Desktop/YOUTUBE) — never mix them.

**Brand law:** Tiger-brand renders obey the `tigerclaw-primitives` repo (`github.com/bbrysonelite-max/tigerclaw-primitives`, local clone `~/tigerclaw-primitives`; git pull first) — real tokens + logo files from the primitives repo, never hand-approximated. Personal-brand styles (journey/coaching/motivational) have their own locked look and are exempt.

**Absorbed engines (2026-07-23):** `machine/voice/` = Brent's text voice (6 named cadences, never-say compliance, gold examples — use for ALL captions/posts), `machine/cadence/` = posting calendar machinery (volume ramp, warm-up, no-repeat usedIdeas ledger in cadence-state.json), `machine/docs/blotato-rest.md` = REST gotchas.

One command turns a prompt into a rendered, gated, queued video:

```bash
# Run on CHEESEGRATER (192.168.0.2) from the LIVE clone — git pull first:
cd ~/Desktop/The\ Brag-Machine/machine && git pull
./claw "VIDEO REQUEST" [flags]
```

Canonical repo: private `github.com/bbrysonelite-max/brag-machine`. The live working clone is **cheesegrater's** `~/Desktop/The Brag-Machine/machine` (a real git clone that pulls from the repo — verified on commit 1294d63, 2026-08-25). The iMac is NOT a render target and its copies (its own `~/Desktop/The Brag-Machine`, Dropbox `Browser-Claude`, iCloud `Share Folder`) are stale remnants — never run those (grounded 2026-08-25; the two machines' Desktops do NOT sync).

## Route the subject to a style

| Brent asks for | Flag | Notes |
|---|---|---|
| Tiger Claw / product content | (none — HOUSE-STYLE default) | locked brand |
| Motivational quote | `--style motivational` | one quote, huge type, vertical default |
| Coaching / teach one thing | `--style coaching` | pain → shift → numbered steps |
| Any business / website promo | `--style business-promo` | put the business's name, URL, real copy, and brand color IN the prompt; always pass `--cta <url>` |
| Positive / gratitude / personal note | `--style positive-post` | gentle motion; personal ones are ALWAYS `--dry`, never queued |

## Flags

- `--format landscape|vertical|square` (default landscape; vertical for TikTok/Reels/Shorts/phone)
- `--channels x,instagram,tiktok,facebook,linkedin[,youtube]` — **YouTube law (2026-08-25):** youtube is NEVER a default and NEVER goes in DEFAULT_CHANNELS (adapter hard-fails). It posts ONLY to the WTH volume channel "What the Freakin' Hell is Ai" (Blotato account 47853), private-first, explicit per-run only — and only once brag-machine PR #24 is merged (until then the adapter on main still blanket-denies youtube). The main @BrentBrysonaios channel is disconnected from Blotato: manual uploads only, forever.
- `--cta <url>` — end-card link + auto-appended to caption (clickable links live in captions, never in the MP4)
- `--dry` — render only, no posting
- `--at "ISO-UTC"` — schedule; without it, draft mode schedules **+6h** (Blotato has no true drafts — delete in dashboard to cancel)
- `--stitch run1,run2,...` — chain past runs (`machine/runs/`) into one film; free, no brain; formats must match
- `--template tigerclaw-launch` — reuse proven video, zero tokens
- `--draft-quality` — fast iteration render

## Laws of operation

1. **Brain runs cost Claude credits** (claw calls `claude -p`). Template and stitch runs are free. Say which you're doing.
2. **Personal videos** (family, private notes) are always `--dry` and never queued to channels.
3. **Queue as draft by default.** `--live` only when Brent explicitly says so.
4. **Rich prompt beats flags:** the VIDEO REQUEST carries the brief — audience, copy, brand color, URL, what's on the end-card. For business promos, prompt-inject the business's REAL copy; never invent claims.
5. **After a render, open the video** (`open runs/<ts>/out.mp4`) so Brent can approve before anything is queued. To queue an approved dry render without re-paying the brain: `./adapters/blotato.sh <out.mp4> <caption.txt> <channels> "" draft`.
6. Every run logs to `ledger.jsonl`; past runs in `runs/` are the b-roll/stitch library.
7. Node: the machine pins Node 22 via `machine.env` — don't "fix" node versions globally.
8. Secrets (2026-08-25): the Blotato key lives in ONE place — the `BLOTATO_API_KEY=` line under `### Blotato` in `~/Desktop/GitSync/CREDENTIALSUPDATED08182026.md` (`~/Desktop/GitSync/kloop.env` is a SYMLINK to it, which is what the adapter reads; the folder syncs to cheesegrater). Rotate by editing that one line only. Never echo it; the key contains `+`/`/`/`=` so never extract with `[A-Za-z0-9_-]` regexes.

## Wow features to reach for

- On-screen URL end-card + caption link (`--cta`) to funnel into the backend/mailing list
- Stitch a themed compilation from past runs (`--stitch`)
- The brain has the full HyperFrames skill suite installed (motion-doctrine, cut-the-curve, seam-craft…) — ask for cinematic moves in the prompt ("zoom-through seam", "waterfall entry", "stat count-up") and it can execute them.
- New subject = new file in `style/` copying an existing one's structure. Commit + push to the repo when adding one.
