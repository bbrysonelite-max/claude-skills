# WTH Campaign — Blotato mechanics (field-level)

Loaded when actually grounding or shipping. Laws live in SKILL.md; this is the how.

## Grounding the queue (Step 1)

Read live via `blotato_list_schedules`, paginating on `cursor` until exhausted. Cached counts rot
within hours.

- **Count UNIQUE first-line captions per day, NOT rows.** One piece fans to up to 6 surface-rows;
  counting rows makes a 1-piece day read as 6 (RUNBOOK §1 trap 3).
- Group by `scheduledAt[:10]`.
- Piece identity = the first line of `draft.content.text`.
- Surface = `draft.accountId`. The two X accounts share platform `twitter`, so key surfaces on
  **account**, never on the platform string.
- **runway** = furthest scheduled day − today (UTC). Also compute per-day unique-pieces and
  surface-fan.

## Shipping (Step 3)

Slots: **16:00 / 19:00 / 22:00Z**, filling forward day by day, only up to today+15.

1. `blotato_create_presigned_upload_url`
2. **curl PUT** the local `.mp4` to that URL
3. `blotato_create_post` per surface with the caption + the uploaded media, scheduled at the slot

**Pace ~20s between ships. Blotato rate-limits at 30 posts.** Before any retry, verify there is no
partial — a failed post can still have uploaded its media.

## Captions — exact format (amended 2026-08-25; verdict: nothing fulfills CLAW comments on X)

- **X (@brentbryson, @pebobryson801):** NO DM promise — nothing watches X comments (Claw Catcher +
  LinkDM are Meta-only). The caption carries the book link directly:
  `What the freakin' hell is X? <def>.` then
  `🐯 Free guide — 5 AI Agents that will 3x Your Business:` + the stan.store book URL.
- **IG / FB:** opener + `Comment CLAW` invite is allowed — Claw Catcher watches these, the
  comment→DM loop is real there.
- **TikTok / LinkedIn:** book link directly, no DM promise (nothing watches comments).

## Verification levels (Step 4)

- **API status** — `blotato_get_post_status` returns published/scheduled + a URL.
- **Media-behind-post** — md5 the uploaded/CDN media against the local `.mp4`.
- **Human eye** — Brent's job; flag which pieces still await his eyes.

## Burned-terms guard

```bash
~/Desktop/The\ Brag-Machine/machine/scripts/burned.sh check "<term>"   # exit 0 safe · exit 1 BURNED
~/Desktop/The\ Brag-Machine/machine/scripts/burned.sh add "<term>" "<YYYY-MM-DD>"
```

Registry: `~/Desktop/The Brag-Machine/machine/campaigns/wth/burned-terms.tsv`. Local, no network or
credential, so there is NO excuse to skip it. As of 2026-08-25 it holds 71 terms; 11 of them shipped
more than once before this guard existed (`parameter` went out 3x, most recently 2026-08-24). That is
the failure this prevents.
