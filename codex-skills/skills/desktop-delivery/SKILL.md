---
name: "desktop-delivery"
description: "Whenever a document is produced for Brent to READ or REVIEW \u2014 a spec, a PRD, a plan, a design doc, a report, an audit \u2014 copy it to his Desktop the moment it's ready, without being asked. He reads from the Desktop, not from repo paths. Invoke automatically any time you hand him a document for review; also when he says \"put it on my desktop\", \"where's the doc\", or \"so I can find it\"."
---

# desktop-delivery

Brent reads documents from his **Desktop**, not from `docs/superpowers/specs/...`
paths buried in a repo. He has asked for this "a hundred times" (his words,
2026-07-06). A review request that ends with only a repo path is an unfinished
delivery.

## The rule

The moment you ask Brent to review a document — spec, PRD, plan, report, audit,
design doc — **copy it to `/Users/brentbryson/Desktop/` in the same turn.** Not on
request. Automatically.

## How

1. `cp <repo-or-scratch path> "/Users/brentbryson/Desktop/<Human Name> <YYYY-MM-DD>.md"`
   - Human-readable filename, Title Case, date included — e.g.
     `Seat Wiring Spec 2026-07-06.md`. Never the repo's kebab-case filename.
2. Verify the copy landed (`ls -la` the target) before telling him it's there.
3. Tell him the exact filename so he can find it on a crowded Desktop.
4. The repo copy stays canonical. The Desktop copy is a READ copy — if he marks it
   up or the spec changes after review, reconcile INTO the repo copy and re-deliver;
   never let the two silently diverge (say which is newer if they do).

## Scope

- Applies to documents FOR Brent's eyes: anything you'd say "please review" about.
- Does NOT apply to code files, internal scratch notes, or docs he didn't ask to
  read and you aren't asking him to.
- One eye, short replies still applies to the chat message — the Desktop copy is
  where the full document lives.
