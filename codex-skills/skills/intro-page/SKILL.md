---
name: "intro-page"
description: "Builds a private, dignified one-page introduction/credibility website for a specific high-value recipient (e.g. introducing Brent to an incoming CEO, a leader, or a partner), then publishes it permanently to a custom domain. Use when Brent wants to introduce himself to someone important without reciting his r\u00e9sum\u00e9 on a call, asks to \"make an intro page / one-pager / credibility page / about-me link\" for a named person, or wants a clean link to hand someone. Defers visual design to frontend-design and any fact-finding research to deep-research."
---

# Intro Page

A one-page site that edifies Brent two ways — his history, and the craft of the page itself — so the
recipient knows who he is before he says a word. Private (noindex), handed to one person, not public SEO.

## Workflow (create a todo per step)

1. **Brainstorm first.** This is creative work → run `brainstorming`. Pin the single goal (almost always:
   *begin a relationship*, never put the recipient on the defensive) and the BEFORE / DURING / NOW spine.
2. **Gather evidence across Brent's machines** (see Gathering below).
3. **Split public vs private — ruthlessly** (see The Line below). This is the most important step.
4. **Verify every claim** that a sophisticated reader could check. Wrong dates/titles in front of a lawyer
   or executive sink credibility. Use `deep-research` for anything external; correct Brent's framing kindly
   but firmly when the record contradicts it.
5. **Design + build.** Run `frontend-design` for a distinctive, non-templated look — keep the visual fresh
   each time, don't reuse a template. Concise, single-scroll, responsive, accessible.
6. **Publish safely** (see Safe Publish below). Then verify live, on the real URL, ideally on mobile.

## Gathering (Brent's network)

Use the **Network Map in MEMORY.md** for machines/IPs. SSH the iMac as `brentbryson@<imac-ip>` with
`~/.ssh/trashcan`; Birdie as `birdie@<birdie-ip>` (same key). Things that bit us before:

- **Apple Mail** lives at `~/Library/Mail/V*/.../Messages/*.emlx`. A sent message can be a `.partial.emlx`
  stub (body not cached) — the full version is often a PDF/docx **attachment** in the same message folder.
- **Parse an emlx**: strip the first line (a byte count), then it's RFC822:
  `python3 -c "import email,sys;raw=open(sys.argv[1],'rb').read();print(email.message_from_bytes(raw[raw.find(b'\n')+1:]))" file.emlx`
- **Dropbox 0-byte gotcha**: online-only files show as **0 bytes** on disk (placeholders). A real copy
  often exists elsewhere (Mail attachment, Messages attachment, another machine) — keep searching, don't
  publish or trust the 0-byte file.

## The Line — public vs private

ON the page (edifying): tenure, rank, awards, real numbers Brent owns, legitimate endorsements, what he
builds now. The page does the bragging so he doesn't have to.

OFF the page → save to a private `resources/` folder for the **conversation/call-prep**, never the site:
grievances, anything whose *motive* is unprovable, an ex-spouse's name, financial hardship, medical/personal
crises (one neutral line max, e.g. "a rough patch"). When in doubt, it's a call topic, not page content.

## Safe Publish (never leak the private files)

The project folder holds private resources + raw source images. **Never publish the project root.**

1. Build an **isolated clean dir** outside the project (e.g. `~/sites/<name>/`) with ONLY `index.html` +
   the few safe assets.
2. **Bake out cropped images** as their own files (e.g. crop a pin from a certificate that also shows a
   name) — never ship the full source image and CSS-crop it; the full file is still fetchable.
3. Deploy from that clean dir: `cd ~/sites/<name> && vercel deploy --prod --yes` (CLI is logged in).
4. **Verify before sharing**: every safe path returns `200`; every sensitive path (`/resources/...`,
   the uncropped image, `/SPEC.md`) returns `404`. Confirm with `curl -s -o /dev/null -w "%{http_code}"`.
5. **Custom domain** (Vercel + Namecheap apex): `vercel domains add <domain>` and `www.<domain>`, then in
   Namecheap → Advanced DNS, delete parking rows and add: `A  @  76.76.21.21` and
   `CNAME  www  cname.vercel-dns.com` (leave nameservers alone). DNS ~10–30 min; Vercel auto-issues HTTPS.
   Poll `https://<domain>` until 200 before telling Brent it's live.

## The text, not just the page

Offer a short, warm text/email to send WITH the link — it points to the page and asks only to connect.
Never lead a stranger with asks; the asks are for the conversation the page earns.

## Codex Runtime

Use the installed `browser-use:browser` or `vercel:agent-browser` skill; preflight by checking installed skill availability before browsing.

Never expose or print secret, credential, or token values.

Mandatory dependencies:
- `SSH website host access`
- `browser automation`

Preflight each dependency using MCP/app capability discovery, CLI availability/version checks, read-only filesystem or Git checks for repositories, and provider auth-status commands without printing secrets, credentials, or tokens.
If any mandatory dependency is unavailable, stop and report a concise blocked state naming the missing dependency and the next action needed.
