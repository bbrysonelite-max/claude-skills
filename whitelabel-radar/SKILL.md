---
name: whitelabel-radar
description: Turns a 30-day trend pulse into a segmented, contactable white-label / group-sale target list of network-marketing leaders for Brent's Tiger Claw. Chains the last30days skill (the pulse) to tiger-leader-hunt (deep scoring). Use when Brent says "whitelabel radar", "find white-label partners / targets", "who can I white-label Tiger to", "turn this trend into leads/targets", or wants to find NM coaches/trainers/authors to resell a branded Tiger to. Defers trend research to last30days and leader scoring to tiger-leader-hunt.
---

# White-Label Radar

Find NM leaders who already sell AI/recruiting education to their own teams, and pitch them a
white-labeled Tiger Claw they resell as their own. The model: **they teach AI; you give their
students the actual agent, branded as theirs.** Brent's 36-year Team Elite record (brentbryson.ai)
is the door-opener.

> **Pattern note:** this is a *template* for last30days-based use-case skills — run the pulse, extract
> the right entities, segment, act. Clone it for other verticals/intents (recruits, partners, buyers).

## Workflow (one todo per step)

1. **Pulse — run `last30days`.** Default angle: `AI for network marketing and direct selling`. Other
   angles: `AI sales agents`, `network marketing recruiting AI`, `direct selling AI tools`. Take the
   angle from Brent if he gave one.
   - **REQUIRED on this machine:** the engine fails with `SSL: CERTIFICATE_VERIFY_FAILED` unless certifi
     is wired in. Before running, export it:
     ```bash
     python3.14 -m pip install --user --quiet certifi 2>/dev/null
     export SSL_CERT_FILE="$(python3.14 -c 'import certifi; print(certifi.where())')"
     ```
     Then run last30days normally (it inherits the env). Without this, every source returns 0 items.
2. **Extract LEADERS, not audiences.** From the result, pull the named **channel owners / creators**:
   YouTube channels, X handles, IG/TikTok creators, book authors. **Do NOT harvest commenters** -
   mass-scraping viewers is ToS-gray and against Brent's public-only compliance line. The target is the
   leader; their audience is reached *through* the white-label, later.
3. **Segment** each leader:
   - **Tier A — go now:** mid-size NM coaches already selling AI/recruiting education (courses,
     challenges, "how to use AI" content), reachable, real audience. Ideal white-label fit.
   - **Tier B — marquee, long game:** the big names (e.g. Eric Worre / Network Marketing Pro). Warm
     intro only (Brent's upline / Jeff Mack), never cold.
   - **Competitors — watch, don't pitch:** AI-sales-agent products (e.g. CallLoop / @polsia), MLM
     software vendors. Note them as competitive signal, not partners.
4. **Find the PUBLIC contact path** for each Tier A/B target via WebSearch — one-by-one, public only:
   website contact/booking page, YouTube "About" business email, LinkedIn, IG DM. Never a scraped blast.
5. **Write the dossier** to `~/Desktop/whitelabel-target-dossier.md` (update if it exists): a table per
   tier (name · where · what they sell · contact path · tailored angle), plus a leader-to-leader
   outreach template that opens with genuine reference to their work, states Brent's Team Elite
   credibility, links **brentbryson.ai**, and offers a 15-minute white-label demo. Value-first, no grind.
6. **Update the pipeline tracker** at `~/Desktop/partner-pipeline.md`: append any genuinely-new target
   as a `new` row (target · tier · channel · status · last touch · next action · notes). NEVER overwrite
   an existing row's status - only add new ones and append a dated line to the Activity log.
   **Then hand Brent the action the frictionless way** — he is phone-first and hates copy-paste / markdown:
   - **Emails (the default):** queue a FINISHED draft straight into his Gmail Drafts. Write the body
     (message + signature) to a temp file, then run:
     `python3 ~/.tiger/draft_email.py --to "<addr>" --subject "<subj>" --body-file <tmp>`
     It appears in his phone Gmail → Drafts → he taps Send. NO paste-blocks, NO Reminders for emails.
     **Batch it:** for a multi-target run, queue ALL the drafts in one pass so he sends a *stack*, not
     one-at-a-time. (Mechanism + app-password handling: see memory `project_gmail_draft_pipeline`.)
     Only fall back to a paste-ready To/Subject/Body block in chat if the draft pipeline is unavailable.
   - **Non-email actions** (a call, a decision, a real-world to-do): add to the Apple **"DO THIS"**
     Reminders list via `osascript` (syncs to his iPhone, voice-addable). Do NOT use `~/Desktop/DO-THIS.md`
     markdown — he never opens markdown.
   - Never let a manual step live only in chat.
7. **Hand off to `tiger-leader-hunt`** for deep scoring/enrichment of the Tier A/B list (leverage,
   team size, reach). This skill builds the seed list; tiger-leader-hunt ranks and deepens it.

## Outreach template (leader-to-leader, no grind)

> [Name] - I saw your [specific video/post] on AI for [recruiting/lead-gen]. You're teaching the right
> thing. I'm Brent Bryson - 36 years, Team Elite at Nu Skin - and I built the agent your students are
> looking for: it does the follow-up, books the call, keeps every lead warm. Here's me: brentbryson.ai.
> I'd love to show you a white-labeled version you could put your name on for your team. Worth 15 minutes?

## Out of scope (point elsewhere)
- **"Show up as the top voice"** is a *content* track, not this skill - use `cadence` / `write-content`,
  and genuinely engage on these leaders' posts before pitching.
- Deep per-leader scoring → `tiger-leader-hunt`. Trend research → `last30days`.
