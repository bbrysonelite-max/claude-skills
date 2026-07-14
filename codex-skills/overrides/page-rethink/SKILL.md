---
name: "page-rethink"
description: "Use when an existing production web page (tigerclaw.io, brentbryson.ai, any live site) \"reads like a wall of text\", visitors wouldn't know what they're reading, the copy has too much \"so what\", Brent asks for design/copy mockups or \"other options\" for a page, or a page rethink needs to ship without disrupting live wiring. Not for brand-new sites (use design-consultation or intro-page) and not for bugs (use production-debugging-loop)."
---

# page-rethink

Rethink an existing live page from verified product, brand, and repository truth. Mock up locally before production and change one review note at a time.

## Codex Runtime

- **Dependencies:** browser automation; target website repository
- `browser automation`
- `target website repository`
- **Execution:** Operate directly in the main Codex agent.
- Use `browser-use:browser` or `vercel:agent-browser` for live-page inspection and screenshot verification.
- Never print, log, or expose secret values.

## Inputs and Preflight

1. Require the live URL, intended audience, user concern, and authority to inspect the serving repository.
2. Open the live page with an installed browser skill. Capture rendered text and viewport screenshots; do not infer a JavaScript page from server HTML alone.
3. Verify which repository serves the domain. Read its `AGENTS.md`, launch guardrails, deploy rules, metadata constraints, and prohibited-copy checks.
4. Read the actual brand book and primitives. Copy token values and component rules exactly.
5. Ground every product claim in current code and canonical product docs. Keep live pricing unchanged unless directed because Stripe configuration may be external.

## Procedure

1. Diagnose the page with the Reading Laws:
   - Label first: the first screen says what the page is.
   - Headlines sell and paragraphs support; a headline-only skim explains the offer and value.
   - Words tell and demos sell; prefer the real product in use.
   - Explain proof and insider terms for civilians.
   - Name nouns instead of relying on unanchored pronouns or metaphors.
   - Use history as evidence, not the spine; lead with the future.
   - Wire every visible control to a real destination.
   - Keep body type readable, normally 15 to 17.5px and never below about 13.5px.
   - Preserve payment, checkout, compliance, disclaimers, and sacred wiring verbatim.
2. Build two or three local static variants using a token-true mockup: real tokens, fonts, assets, content, and functioning links. Do not touch the live site.
3. Verify every mockup yourself with browser automation at desktop and mobile `375x812`. Capture screenshots, inspect rendered text, and confirm `document.body.scrollWidth <= 375` on mobile.
4. Present initial variants together. After review begins, apply exactly one note per exchange, reload the reviewed page, re-verify both viewports, and keep the durable mockup copy current.
5. Ship only after an explicit instruction. Create a branch and PR, make the smallest production edit, preserve metadata and sacred wiring, and run repository lint, build, tests, and prohibited-copy checks.
6. After deployment, poll for a new-copy marker and verify the production URL at desktop and `375x812`. Confirm mobile width, links, metadata, compliance text, and rollback readiness before declaring success.

## Safety and Errors

- Mockups before production. Never treat design approval as permission to deploy.
- Do not approximate brand tokens, expose dark features, alter checkout, invent prices, or ship broken controls.
- Ship surgically and keep changes one-note-at-a-time after review begins.
- If the serving repo, product truth, brand source, or deployment path cannot be verified, stop and report the missing evidence.

## Output Contract

Before shipping, return the diagnosis, evidence sources, mockup paths, and desktop/mobile verification. After an approved ship, return the PR, checks, deployment proof, production desktop/mobile screenshots, width result, metadata and wiring verification, and any remaining unverified item.
