# Active Skills Index

Audited & verified: 2026-08-29 (library campaign). Count: 179 loadable skills on the live shelf, byte-identical on both Macs.
House standard: `~/.claude/skills/docs/HOUSE-STANDARD.md` — every bespoke skill written/reviewed to it 2026-08-29 (two merges, 25 rewrites, adversarial + mechanical review).
Source of truth: `~/.claude/skills/` — now **synced hourly between the iMac and the cheesegrater** (skillsync, manifest-verified; delete on BOTH Macs to retire a skill). Stores: `~/.agents/skills` (HyperFrames canonical), `~/claude-skills` (managed collection).
Superpowers process skills (brainstorming, TDD, systematic-debugging, writing-plans, …) now live in the **superpowers plugin**, not on this shelf — still invocable, no longer indexed here.

## 1. Engineering and execution

- **the-loop** — Brent's canonical build-and-debug pipeline with hard role separation (staffed by tiny-team, §11).
- **production-debugging-loop** — closed-loop debugging: evidence → fix → proof → regression guard.
- **production-gate-audit** — audit production readiness and CI/branch-protection enforcement.
- **code-reviewer** — review local changes or PRs for correctness and standards.
- **pr-creator** — create PRs that follow the repo's templates.
- **prototype** — throwaway prototypes to flesh out a design before committing.
- **docs-writer** — writing/reviewing /docs and repo .md files.
- **optimize** — audit the instruction layer agents actually read (CLAUDE.md, rules, hooks).
- **kloop** — optimize a text asset against a measurable score (Karpathy loop).
- **learn** — manage project learnings.
- **gemini-api-dev / gemini-interactions-api / gemini-live-api-dev** — build against the Gemini APIs.

## 2. Quality, truth, and risk

- **ground-truth** — the epicenter: never state or act on what you haven't observed live.
- **fitfo** — F.I.T.F.O., Brent's universal agent doctrine: figure it out, never stop silently.
- **blind-spots-audit** — surface missed questions, assumptions, and agent errors.
- **failure-modes** — FMEA + pre-mortem + red-team sweep of any target.
- **grill-me** — relentless plan interrogation until shared understanding.
- **grill-with-docs** — grilling that also updates CONTEXT.md/ADRs inline.
- **unfinished** — enumerate everything UNFINISHED / UNVERIFIED / UNCONFIRMED from ground truth.
- **system-status-triage** — read-only triage when the Tiger dashboard goes YELLOW/RED.

## 3. Research, signals, and leads

- **agent-reach** — internet research through the right platform backends.
- **last30days** — what people actually said about a topic in the last 30 days.
- **blueprint** — define the golden lead and money-in-hand buyer before building.
- **mine** — Stage 2 of The Refinery: raw ore for a vertical (absorbed signal-mine 2026-08-29; proven tracks in its references/).
- **refine** — refine mine ore into resolved, contactable individual leads.
- **allsup-leads-ssdi** — monthly SSDI/SSI claimant lead batch (proven process).
- **allsup-leads-veterans** — veterans benefits-gap lead batch.
- **network-reactivator** — reactivate a dormant warm market one question at a time.
- **tiger-leader-hunt** — leader discovery AND white-label/group-sale targeting (absorbed whitelabel-radar 2026-08-29).
- **ego-browser** — agent-friendly Chromium for browsing, forms, scraping, QA.

## 4. Cloud, ops, and machine plumbing

- **loading-secrets** — canonical per-machine secret paths; load keys by name, never see values.
- **cloud-run-reauth** — restore gcloud access to TigerClaw prod; raw secret bytes.
- **ship-it** — take a TigerClaw PR from green to live with deploy verification.
- **tigerclaw-daily-checks** — Tiger Claw operational health checks, one verdict.
- **gws-shared / gws-workflow / gws-workflow-email-to-task / gws-workflow-file-announce / gws-workflow-meeting-prep / gws-workflow-standup-report / gws-workflow-weekly-digest** — Google Workspace CLI patterns and cross-service workflows.
- **here-now** — publish files/folders to the web instantly.

## 5. Knowledge, documentation, and brand

- **closing-ritual** — end any session clean: merged, green, docs true, memory saved.
- **context-keeper** — append-only per-session flight recorder in the project.
- **doc-keeper** — reconcile any project's living docs with reality (one docs PR).
- **tiger-doc-keeper** — the Tiger Claw repo's document keeper (SOTU/PROGRESS/ADRs).
- **truth-keeper** — keep the universal + per-project truth layers zero-drift.
- **vault-hygiene** — vault structure, indexes, and metadata maintenance.
- **desktop-delivery** — every reviewable doc lands on Brent's Desktop.
- **handoff** — compact the conversation into a handoff doc for another agent.
- **graphify** — knowledge-graph any codebase or content; query it.
- **claude-memory-index / -search / -debug / -status** — commit-history memory over repos.
- **intro-page** — private credibility page for a specific high-value recipient.
- **page-rethink** — rethink an existing production page around reader needs.
- **the-rebuild** — load the strategic context of Brent's business rebuild.
- **tiger-whitepaper** — branded Tiger Claw white papers (print-ready PDF).
- **two-brents-brand** — the AI-is-Electricity / Alien Abduction brand system.
- **i-have-adhd** — shape output for an ADHD reader: next action first, numbered steps.
- **hallmark** — anti-AI-slop design for pages, audits, redesigns.

## 6. Harness and skill maintenance

- **skills-librarian** — audit the shelf, reconcile this index, quarantine cruft, mirror backup.
- **skill-miner** — mine session transcripts for routines worth becoming skills.
- **write-a-skill** — create new skills with proper structure.
- **cmux / cmux-workspace / cmux-browser / cmux-settings / cmux-customization / cmux-keyboard-shortcuts / cmux-markdown / cmux-diagnostics** — drive and configure the cmux terminal app.

## 7. HyperFrames foundations

- **hyperframes** — mandatory entry point; routes all video/animation work.
- **hyperframes-core** — the composition contract.
- **hyperframes-cli** — the CLI development loop.
- **hyperframes-animation** — motion rules, blueprints, transitions, runtime adapters.
- **hyperframes-creative** — non-animation creative direction (design spec, palettes, narration).
- **hyperframes-keyframes** — seek-safe keyframes, GSAP/WAAPI/FLIP/SVG systems.
- **hyperframes-registry** — install and wire registry blocks/components.
- **hyperframes-media** — TTS, BGM, transcription, background removal, captions prep.
- **motion-doctrine** — GATEWAY motion law; load first before composing.
- **cut-the-curve** — the velocity-matched seam catalog.
- **seam-craft** — render-correctness doctrine for scene seams.
- **captions-overlay** — caption model doctrine (drop / rail / embed).
- **oversized-cursor** — house oversized-cursor treatment.
- **media-use** — Agent Media OS: resolve any media asset to a frozen local file.
- **figma** — import Figma content into motion-ready compositions.
- **remotion-to-hyperframes** — port Remotion compositions to HyperFrames.

## 8. Video and presentation workflows

- **general-video** — longform, multi-scene custom compositions.
- **faceless-explainer** — text/topic → visual explainer video.
- **product-launch-video** — product/SaaS launch and promo videos.
- **website-to-video** — general site tour/showcase videos.
- **pr-to-video** — pull request → code-change explainer.
- **changelog-video** — weekly changelog → branded video.
- **music-to-video** — music track → beat-synced video.
- **motion-graphics** — short design-led motion pieces.
- **slideshow** — interactive HyperFrames presentations and decks.
- **embedded-captions** — designed captions on existing talking-head footage.
- **graphic-overlays / talking-head-recut** — package existing footage with overlay cards.
- **heygen-avatar / heygen-video** — persistent avatars and presenter videos (AI-Brent lane).
- **watch** — ingest and analyze any video (frames + transcript).
- **longform-video** — the PROVEN mixed longform format for @BrentBrysonaios (on-camera + faceless beats + clone; proven 2026-08-29 on flavored-agent v5).
- **hyperframes-audio** — mix audio already placed in a composition (fades, ducking, buses).

## 9. Brag Machine and campaigns

- **write-content / blotato-post / cadence** — ai-social-system repo skills (symlinked; repo-managed).

- **brag** — turn the current project site into a launch video.
- **brag-machine** — the claw pipeline: prompt → branded beat-synced video → queue to social.
- **brag-one** — render ONE video end-to-end (brief → render → review → queue).
- **brag-two** — pin rendered videos into longer films / YouTube cuts.
- **brag-week** — batch day: a full week of content in one sitting.
- **brag-personal** — personal message videos, gift files only (never queued).
- **brag-music** — source and lock licensed music themes by ear.
- **brag-voice** — Brent's local Voicebox voice clone for narration.
- **wth-campaign** — daily doer keeping the WTH queue in the 7–15 day band via Blotato.

## 10. Business operations

- **beacon-protocol** — MANDATORY operating law for all BEACON/visibility work (GEO/SEO, citations, brentbryson.ai, channel packaging).

- **brents-daily-checks** — the cross-business daily control panel, one portfolio verdict.
- **brent-cfo** — reconcile bank + PayPal into the Straight Truth sheet.
- **brent-cro** — proactive daily revenue brief across all lanes.
- **brent-office-manager** — one home per document, Open Loops list, Monday sweep.
- **alienprobe-product-puck** — Alien Probe product discovery and 90-day planning.

## 11. Memory and grounding (Jumbo)

- **tiny-team** — the Jumbo org chart (adapted from its upstream): Scout/Builder/Reviewer + Agent Memory as a duty every role owes; staffs the-loop.
- **visit-jumbo** — session-opening grounding brief from shared memory.
- **visit-jumbo-deep** — full per-lane grounding dossier.
- **jumbo-health** — GO/RED health check of the Jumbo memory system.

## 12. gstack suite

Managed by gstack; upgrade with **gstack-upgrade**. Router: **gstack** (folder `_gstack-command`) + **open-gstack-browser** (folder `connect-chrome`).
- Reviews & planning: **office-hours / plan-ceo-review / plan-eng-review / plan-design-review / plan-devex-review / plan-tune / autoplan / review / retro / spec**
- Design & docs: **design-consultation / design-html / design-review / design-shotgun / diagram / make-pdf / document-generate / document-release**
- QA & browsing: **browse / qa / qa-only / benchmark / benchmark-models / scrape / skillify / setup-browser-cookies / pair-agent / health / devex-review**
- Ship & deploy: **ship / land-and-deploy / landing-report / setup-deploy / canary**
- Safety & session: **careful / guard / freeze / unfreeze / cso / investigate / context-save / context-restore / codex**
- iOS: **ios-clean / ios-design-review / ios-fix / ios-qa / ios-sync**
- gbrain: **setup-gbrain / sync-gbrain**

---
*Retired 2026-08-29 by merge (quarantined in the dumps, both Macs): signal-mine → mine; whitelabel-radar → tiger-leader-hunt; alias dupe open-gstack-browser. Removed earlier audits (no longer installed anywhere): ai-evaluation-audit, assumptions-audit, codebase-pattern-mapping, documentation-claim-verification, integration-flow-audit, maigret-username-enrichment, requirements-coverage-audit, social-signal-ledger, threat-mitigation-audit. Superpowers process skills moved to the plugin (see header).*
*Known folder↔name mismatches (gstack-managed, left alone): `_gstack-command`→gstack, `connect-chrome`→open-gstack-browser.*
