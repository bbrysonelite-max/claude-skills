# Brent's Skill House Standard — v1 (2026-08-29)

Every bespoke skill on the Claude shelf is written to this. Reviewers grade against it.
Upstream-managed skills (gstack, HyperFrames store, superpowers plugin, vendor CLIs) are exempt — never edited.

## Frontmatter
1. `name:` matches the folder exactly. Letters/numbers/hyphens only.
2. `description:` states ONLY when to use — triggering phrases, symptoms, situations. It never
   summarizes the workflow (agents follow a summarized description instead of reading the body).
   Include Brent's actual trigger phrases in quotes. Third person. Under ~500 chars where possible.
3. If the skill has a legal twin (depth / vertical / surface pair), the description NAMES the twin
   and the boundary: "for X use /twin instead."

## Body
4. Open with the core principle in 1–2 sentences, then the work. No throat-clearing.
5. **Receipts law**: any skill that claims, checks, or ships states its proof format —
   command + output + UTC, or the word UNVERIFIED. Inherited from /ground-truth; restate only the
   skill-specific receipt, don't re-teach the doctrine.
6. **Halt law**: the only end states are DONE-with-receipt or one decision-ready question
   ("A or B, I recommend A because X"). Inherited from /fitfo; don't re-teach it.
7. Hard-won rulings stay: dated evidence, Brent's quoted rulings, gotchas with the date they bit.
   These are the skill's value — a rewrite that launders them out is a defect.
8. Paths, ports, hosts, and variable names are stated exactly and were verified at write time;
   anything unverified is labeled UNVERIFIED inline.
9. Secrets: never a value in a skill. Point to /loading-secrets by name.
10. Output shaping: reports the skill produces follow Brent's reading laws — lead with the verdict,
    short lines, no walls, no jargon chains.
11. One excellent example beats three mediocre ones. No multi-language dilution.
12. Length: <200 words for always-loaded/doctrine skills; <500 words for workers; heavy reference
    goes to a references/ file, loaded only when needed.

## Structure
13. One folder, one SKILL.md, supporting files only for reusable tools or heavy reference.
    No .bak files, no drafts, no commented-out corpses — the dump exists for that.
14. Cross-references use the skill name (/name), never file paths, never @-force-loads.

## Estate laws
15. No duplicates: one name loads from one place. Overlap is legal only for depth / vertical /
    surface pairs, and both twins declare each other (rule 3). More than two same-purpose skills:
    merge the good from all into one (Brent's ruling 2026-08-29).
16. Retirement = quarantine to the dump on BOTH Macs in the same breath (skillsync resurrects
    one-sided deletes). Never rm.
17. Every skill change lands in: the shelf (both Macs, verified sync), the SKILLS-INDEX,
    the mirror repo via librarian PR (Brent merges), and Jumbo at slice close.
18. A new or rewritten skill is UNVERIFIED until its first real walk; the tag lives in the
    index entry, not the skill body.
