---
name: page-rethink
description: Use when an existing production web page (tigerclaw.io, brentbryson.ai, any live site) "reads like a wall of text", visitors wouldn't know what they're reading, the copy has too much "so what", Brent asks for design/copy mockups or "other options" for a page, or a page rethink needs to ship without disrupting live wiring. Not for brand-new sites (use design-consultation or intro-page) and not for bugs (use production-debugging-loop).
---

# page-rethink

Rethink a live page's copy and layout the way that shipped tigerclaw.io's chat-demo homepage and brentbryson.ai's "The Intersection" (2026-07-12). Core principle: **ground truth before opinion, mockups before production, one change per exchange.** The live site is never touched until Brent says ship.

## The Workflow

### 1. Ground truth (before any opinion)

- **Live page**: sites are usually JS apps — `curl` shows nothing. Use the gstack browse binary: `B="$HOME/.claude/skills/gstack/browse/dist/browse"`, then `"$B" goto <url>`, `"$B" text`, `"$B" screenshot` (full command list in the /browse skill). Full-page screenshots of scroll-reveal sites render mostly blank; trust `text` + viewport shots.
- **Which repo actually serves the domain**: verify (title match in index.html, vercel.json), don't assume. All repos live under the `bbrysonelite-max` GitHub org — shallow-clone into the scratchpad with `gh repo clone bbrysonelite-max/<repo> -- --depth 1`. Tiger's marketing site is `Tigerclawvebsite-v5`, NOT tiger-claw-v4-core. brentbryson.ai's canonical source is `~/sites/brentbryson-ai` on cheesegrater (`ssh cheesegrater`).
- **Brand system**: use the real tokens verbatim — the brand book page (e.g. tigerclaw.io/brand) and the primitives repo (`bbrysonelite-max/tigerclaw-primitives`: tc-* vars in `client/src/index.css`, component recipes in `client/src/pages/Home.tsx`). Brent's words: "Don't get me off brand. You've got to use the brand book and my primitives." Hand-derived approximations get rejected.
- **Repo law**: read AGENTS.md / LAUNCH_GUARDRAILS.md first — locked positioning, banned terms, metadata that must not change, deploy workflow.
- **Product truth**: claims must be grounded in the product repo (`tiger-claw-v4-core`: SOTU, BIG-PICTURE, ARCHITECTURAL_DECISIONS, code). Never market dark/internal features. Amending a locked decision (e.g. ADR 013's headline) needs a recorded amendment PR.
- **Prices are Stripe config, not code**: dollar amounts on pricing pages map to Stripe price IDs set via env (e.g. `STRIPE_PRICE_BYOK`), so the repo can't confirm them — keep displayed prices identical to what's live unless Brent says otherwise, and remind him of his own guardrail: "Stripe dashboard copy must be updated manually when site copy changes."

### 2. Diagnose with the Reading Laws

Skim the page reading ONLY the big type — that's what a visitor absorbs. Then check every law:

| # | Law | Test |
|---|---|---|
| 1 | **Label first** | Does the first screen say what the page IS? "A lot to read before I know what I'm reading" = fail. |
| 2 | **Headlines sell, paragraphs support** | Headline-only skim must answer: what is it, what problem, what's in it for me. Paragraphs ≤ 1 supporting line. |
| 3 | **Words tell, demos sell** | Show the product working (chat thread, real screenshots) instead of describing it. |
| 4 | **Explain for civilians** | "You and I know, they don't. Nobody knows about AI." Every proof artifact (GitHub wall, Wispr stats) needs what-it-is + a "why it matters" line. Gloss every insider term (ACT!, GitHub, operator). |
| 5 | **No unanchored pronouns** | "One… the other… the intersection" — name the nouns. If Brent asks "the ground floor of what?", the metaphor failed. |
| 6 | **Future over past** | History is evidence inside the story, never the spine. Never lead with Brent's age. |
| 7 | **Everything works** | No dummy nav/menus/buttons in anything he'll click ("how none of them work there — dummies"). Anchors, tel:, mailto: real. Mockup CTAs may LINK to real live destinations (e.g. /start, tigerclaw.io) — linking to checkout is fine; changing checkout is Law 9's line. |
| 8 | **Readable type** | Nothing under ~13.5px; body 15–17.5px. Bigger, not brighter. Brent has one eye and a 35-inch screen. |
| 9 | **Sacred wiring** | Payment/checkout surfaces untouched. Compliance/disclaimer text preserved verbatim (may move into a LegalDrawer — accessible but put away). |

### 3. Mockups (local only)

- Static HTML in the session scratchpad, real tokens + Google Fonts, real assets copied beside the file.
- Verify with browse screenshots yourself BEFORE showing him — desktop AND `viewport 375x812` (check `document.body.scrollWidth` ≤ 375; a page with no `@media` block shipped broken to production once).
- Open in Chrome with `open -a "Google Chrome" <file>` — bare `open` gets hijacked by cmux panes. If he can't see it, activate the exact tab:
  ```bash
  osascript -e 'tell application "Google Chrome"
    activate
    repeat with w in windows
      set i to 1
      repeat with t in tabs of w
        if title of t is "<exact title>" then
          set active tab index of w to i
          set index of w to 1
        end if
        set i to i + 1
      end repeat
    end repeat
  end tell'
  ```
- Multiple mockups → ONE combined page with sticky orange divider banners (iframes), so there's nothing to hunt for.
- Copy the current version to `~/Desktop/<Project>-Mockups/` — scratchpad dies with the session.

### 4. Iterate one note at a time

Presenting 2–3 initial variants together (on the combined divider page) is fine — that's the opening menu, not batching. Batching starts AFTER he begins reviewing: from his first note onward, apply exactly one note per exchange, reload his tab via the AppleScript above, sync the Desktop copy, answer in 2–4 short sentences. The mockups that iterated one note at a time shipped; a re-proposed batch got "this is a mess."

### 5. Ship surgically (only on his explicit "ship it")

- Branch → PR. Never push main (repo rules; merge may need `--admin` and all PR comment threads resolved — bot findings like Cursor's are often real, fix them).
- Know the deploy path before merging: Vercel git-integration (merge = deploy, e.g. Tigerclawvebsite-v5) vs manual CLI (`ssh cheesegrater 'zsh -l -c "cd ~/sites/<site> && vercel deploy --prod --yes"'` — needs a login shell for node).
- Run the repo's own verification (lint, build, prohibited-copy grep) before claiming done.
- Verify LIVE: poll the domain for a new-copy marker (`until curl -sL <url> | grep -q "<new headline>"; do sleep 15; done` as a background task), confirm metadata unchanged, keep rollback in mind (Vercel previous deployment).
- Update memory: what shipped, and any new copy law he taught.

## Common Mistakes

| Mistake | Reality |
|---|---|
| Styling from memory of the brand | Clone the primitives repo; copy token values verbatim |
| `curl` to read the page | JS apps render nothing server-side; use browse |
| Leading mockups with slogans/metaphors | Slogan moves to a pull-quote; the label line leads |
| Impressive stats with no explanation | Stats without a "why it matters" line mean nothing to civilians |
| Dead links in a mockup he'll click | Wire anchors/tel/mailto even in mockups |
| Shipping copy that outruns the product | Ground every claim in the product repo's current, non-dark state |
| Declaring done after deploy command | Only live-domain verification with the new content counts |
| Reviewing desktop-only | brentbryson.ai shipped with 546px of content in a 375px phone — always test mobile before AND after ship |
