# Tiger Claw White Paper — Reference

## Brand system (the "signature")

Source of truth: the V5 brand book (`~/Tigerclawvebsite-v5`) and the primitives depot
(`github.com/bbrysonelite-max/tigerclaw-primitives`). The build script already encodes
all of this — these values are here so body copy and any tweaks stay on-brand.

**Palette:** base `#0A0A0A` · surface `#1a1a1a` · ink `#050505` · orange `#E8722A`
(CTA/accent/signal) · green `#4ADE80` / deep `#22C55E` (live status) · body gray
`#c4c4ce` · dim label `#6b6b75` · white = emphasis only.

**Fonts:** Bebas Neue (all-caps headers + the **TIGER CLAW** wordmark) · Space Grotesk
(body) · IBM Plex Mono (uppercase eyebrow labels, control numbers, chips).

**Brand laws:**
- **Bigger, not brighter** — size carries emphasis, not extra color. Gray is the default,
  white is emphasis, orange + green are *signals* (never decoration).
- **No emojis. Ever.** Typographic arrows (→) are fine.
- **Benefits, never raw tech names** in marketing/technology papers — say what it does.
- Wordmark **TIGER CLAW**. Default tagline **"Fortune is in the follow-up."**
- Entity: **Mariah Marketing LLC**. Default return email: **support@tigerclaw.io**.

## The three variations — doctrine

### `science`
Reader is an evaluator who distrusts hype. Proof over persuasion. No CTA hard-sell —
a quiet "next step / contact" at most. Suggested arc: **Abstract → Background / Problem →
Method → Results & Evidence (use tables) → Limitations → Conclusion → References**
(use `<ol class="refs">`). Measured voice. Still gets the receipt + numbering.

### `technology` (with some marketing)
Reader is a technical buyer or leader doing diligence. Answers "how does it work, will it
hold up?" — but opens and closes on why it matters. Suggested arc: **What it is → How it
works (architecture, data, security, multi-tenancy/isolation) → What you get → Honest
maturity map (live / built-but-dark / pending, via status chips) → One next step.**
The existing product white paper is the model for the technical sections.

### `marketing` (with some technology)
Reader is the buyer, asking "what's in it for me?" constantly. Lead every section with
benefit in the reader's language; include only enough "how it works" to be believable;
drive to **one** CTA. Warm, direct, short sentences. The Jon Jackson paper (No. 004,
`assets/`) is the reference build.

> Same facts, different reader, different question. Move along the scale by shifting how
> much "how it works" vs. "what's in it for me" leads — not by changing the truth.

## Confidentiality receipt + numbering

- Every paper is issued under a control number: **Tiger Claw White Paper No. NNN**
  (zero-padded, e.g. `004`). Tracked in `LEDGER.md`. Internal only.
- The receipt is **page 2**, rendered light/white so it prints and signs cleanly. The
  build script generates it from the spec — issued-to, issued-by, the nondisclosure
  clause, signature/date/printed-name lines, and a "sign and return by email to" block.
- Override the clause via `spec.receipt.clauseBody` when the context isn't a white-label
  pitch (e.g. a science paper shared with a partner lab). Keep it plain-language; it is a
  good-faith acknowledgment, not heavy legal.
- Omit the receipt only if Brent explicitly says so: set `spec.receipt.include = false`.

## Body authoring — CSS class catalog

Author the body as a fragment of full-page sheets. Each body page:

```html
<section class="sheet dark">
  <div class="body-head"><span class="wordmark">TIGER CLAW</span>
    <span class="pg">Confidential · No. 004</span></div>

  <div class="sec">
    <div class="sec-label"><span class="num">01</span>
      <span class="eyebrow">Section label</span><span class="ln"></span></div>
    <h2>SECTION HEADER IN BEBAS</h2>
    <p class="lead">Opening lead line, slightly larger.</p>
    <p>Body copy. Emphasis with <strong>white bold</strong>, signals with
       <span class="orange">orange</span> or <span class="green">green</span>.</p>
    <div class="card"><div class="q">A pull-quote / key promise in a bordered card.</div></div>
  </div>
</section>
```

Other blocks:
- **Status chips** (maturity): `<div class="chips"><span class="chip"><span class="dot green"></span> LIVE NOW · ...</span><span class="chip"><span class="dot"></span> COMING · ...</span></div>`
- **Table** (science/technology): plain `<table><tr><th>…</th></tr><tr><td>…</td></tr></table>` inside a `.sec` — styled automatically (orange mono headers).
- **References** (science): `<ol class="refs"><li>…</li></ol>`.
- **CTA** (marketing/technology close): `<div class="cta"><p class="step"><strong>1.</strong>&nbsp; …</p>…<span class="pill">Book a call with Brent</span></div>`
- **End tag:** `<div class="endtag">Fortune is in the follow-up.</div>`

Keep ~2 sections per sheet. If a page overflows (an extra blank/overflow page appears),
split a section onto a new sheet or trim margins.

## Spec JSON fields

| field | notes |
|---|---|
| `controlNumber` | e.g. `"005"`. Drives cover stamp, receipt, footers. |
| `variation` | `science` \| `technology` \| `marketing`. Sets the cover kicker if `kicker` unset. |
| `kicker` | optional cover eyebrow override. |
| `recipient`, `recipientLabel` | cover "Prepared for". |
| `author` | default `Brent Bryson`. `entity` default `Mariah Marketing LLC`. |
| `date` | e.g. `"June 27, 2026"`. |
| `title` | inline HTML allowed (`<br/>`, `<span class="orange">`). |
| `subtitle`, `tagline` | tagline default `Fortune is in the follow-up.` |
| `confidential` | default `true` → shows the Confidential · No. NNN stamp. |
| `coverMeta` | optional array `[{label,val}]` to fully control the cover meta grid. |
| `receipt` | `{include, issuedTo, clauseTitle, clauseBody, note, returnEmail}`. |
| `bodyHtmlPath` | path to the authored body fragment (relative to the spec). |
| `outPath` | output PDF path (relative to the spec, or absolute). |
| `chromePath` | override if Chrome isn't at the default macOS location. |

## Render + verify

```bash
node scripts/build-whitepaper.mjs <spec.json>
```

Requires headless **Google Chrome** (macOS default path baked in). The
`CVDisplayLinkCreateWithCGDisplay` warnings on macOS headless are harmless.

**Always verify by reading the output PDF pages as images.** `mdls` page counts can be
stale — trust the rasterized pages. Confirm: cover correct, receipt on one page, no
overflow/blank pages, no emojis, claims labeled honestly.
