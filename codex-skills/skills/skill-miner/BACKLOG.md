# skill-miner BACKLOG

Ledger of skill candidates surfaced by skill-miner. The dedupe memory + lightweight skill map.
Statuses: `proposed` (awaiting Brent) · `built` (exists) · `declined` · `deferred`.
On each run, only unseen routines (or still-`proposed`) should reach the suggestion step.

Seeded from the 2026-06-28 transcript-mining pass (45 sessions, May 28–Jun 28; 3 analysts converged).

| candidate | status | impact | first-seen | evidence | note |
|---|---|---|---|---|---|
| ship-it | built | High | 2026-06-28 | nearly every session (all 3 batches) | merge→CI→Cloud Run deploy→/health-SHA verify; merge gated on --confirm |
| skill-miner | built | High | 2026-06-28 | this pass + the meta-idea | this skill — mine sessions → suggest candidates |
| session-grounding | proposed | High | 2026-06-28 | opens ~every session (b1,b2,b3) | read SOTU/NEXT_SESSION/CLAUDE/AGENTS → ground truth → narrate last 24–48h in his words |
| verify-prior-work | proposed | High | 2026-06-28 | b3 (multiple) | read-only audit that a PRIOR session's claimed work shipped & works live (Playwright), not from "the shape" |
| tenant-isolation-audit | proposed | High | 2026-06-28 | b2 (Debbie leak) | detect cross-tenant fact/lead leak, blast radius read-only, surgical repair |
| youtube-thumbnail | proposed | Med | 2026-06-28 | b3 (repeatedly asked) | deterministic on-brand YouTube thumbnail maker |
| lead-package-pdf | proposed | Med | 2026-06-28 | b3 (Pat/Allsup) | method-stripped branded PDF of a mined lead batch; can reuse tiger-whitepaper engine |
| site-audit | proposed | Med | 2026-06-28 | b1 (tigerclaw.io) | browser SEO/GEO/agent-legibility + UX grade + JSON-LD draft |
| cleaner-lanes-refactor | proposed | High | 2026-06-28 | 6+ sessions (e177a500, af3f3ab9, 03a03ffd, e08d1393, 2fbb7dd2) | test-lock → extract-in-slices → 1 PR/slice → CI → merge; the dominant build methodology, no skill (≠ the-rebuild from-scratch) |
| credential-loader | proposed | High | 2026-06-28 | 6+ sessions (7ae5162a, b68cd7e5, 534f4974, 13fe7c9c, 5690504e) | canonical local key store (~/Desktop/GitSync/kloop.env), validate format, load right key, NEVER echo; cloud-run-reauth is GCP-only. Recurring "wrong/expired/misformatted key" frustration |
| operator-ux-walk | proposed | High | 2026-06-28 | 4-5 sessions (66287382, 5d7293f1, cbab12a6, 2fbb7dd2) | walk a LIVE Tiger app surface as a confused non-technical operator → flag confusing copy/flow/WIIFM. His #1 product priority; ≠ site-audit (marketing SEO) |
| skills-librarian | built | Med-High | 2026-06-28 | 5+ sessions (f6658698, 58c7c210, 2e216d5f, 518047a7) | maintain/dedupe/index the INSTALLED skills folder + SKILLS-INDEX.md. Complements skill-miner. Built 2026-06-28 (audit.py: integrity/inventory/diff-index, IGNORE heygen-skills, never-delete). Found: 86 live vs index's 70, 16 unindexed |
| blind-spots-audit | built | Med | 2026-06-28 | 5 sessions (369cc193, f6658698, 13fe7c9c, 4682932b, 5a58b29f) | agent enumerates what Brent ISN'T asking / what the build missed. Inverse of grill-me. Built 2026-06-28 (7-lens sweep + self-audit + independent-panel escalation; no script — reasoning skill). Exercised live on this session's work |
| operator-onboard | proposed | Med | 2026-06-28 | 3 sessions (cbab12a6, 5d7293f1, b803b836) | onboard a paying founder end-to-end + verify THEIR dashboard shows real non-leaked data + draft a nudge |
| sacred-wiring-guard | proposed | Med | 2026-06-28 | 6+ sessions | enumerate/gate edits against SACRED_WIRING.md before touching protected surfaces |
| dependency-alert-triage | deferred | Med | 2026-06-28 | 2-3 (2bafdfa2, #1217) | sweep repo Dependabot high/mod/low backlog to zero; ≠ change-scoped security-review |
| brand-apply | deferred | Med | 2026-06-28 | overlap | apply Tiger brand to arbitrary artifact — partial overlap with tiger-whitepaper + hallmark |
| verify-deploy-landed | declined | — | 2026-06-28 | overlap | COVERED by ship-it (merge-SHA in /health); migration-column check could fold into ship-it |
| merge-and-verify | declined | — | 2026-06-28 | overlap | COVERED by ship-it |
| failure-modes | built | High | 2026-06-28 | brainstormed (not mined) | comprehensive FMEA/pre-mortem method: sweep 32 failure surfaces (5 bands) of any target → invert each to a designed strength. Distinct from blind-spots (unknown-unknowns). Built 2026-06-28; first run found a real bug in ship-it (deploy watches latest run, not merge-SHA's run) |

<!-- Also already built outside this ledger: tiger-whitepaper, cloud-run-reauth, context-keeper. -->
