---
name: optimize
description: "Use when Brent says \"optimize\", \"audit my instructions\", \"is my CLAUDE.md holding you back\", \"why is the agent ignoring my rules\", \"find misaligned instructions\" — or after any incident where an agent followed a stale rule, ignored a documented one, or acted on a doc from the wrong checkout. Covers the whole instruction layer an agent actually reads: CLAUDE.md, AGENTS.md, .cursor/rules.md, .anti-gravity/rules.md, hooks, settings, and every doc marked \"read first.\""
---

# /optimize — Instruction Layer Auditor

**Documents are testimony. Code, terraform, git and live endpoints are evidence.**

Never validate an instruction file against another instruction file. A doc that says "we use
GKE" proves nothing; `grep google_container_cluster` in terraform proves something.

**Receipts:** every finding carries the command run, what it returned, and UTC. No claim
without an artifact. A claim you could not check is written UNVERIFIED with the command that
would settle it — never softened into a maybe.

## 1 — Inventory every authority

```bash
find . -maxdepth 4 \( -iname "CLAUDE.md" -o -iname "AGENTS.md" -o -iname "rules.md" \
  -o -iname "*.mdc" -o -iname "START_HERE.md" -o -iname "SOTU.md" \
  -o -iname "BIG-PICTURE.md" -o -iname "NEXT_SESSION.md" \) \
  -not -path "*/node_modules/*"
cat .claude/settings.json ~/.claude/settings.json 2>/dev/null   # hooks inject instructions too
ls ~/ | grep -i <project>                                        # sibling/stale checkouts
```

Don't stop at the obvious file. **Sibling checkouts are the #1 source of poisoned
instructions** — settle which repo is real (phase 2) before auditing anything.

## 2 — Ground truth: which repo is real?

```bash
curl -s <prod-health-endpoint>          # or WebFetch — get the deployed gitSha
git cat-file -t <deployed-sha>          # "bad object" => THIS IS NOT THE REAL REPO
git branch -a --contains <deployed-sha>
```

Run in **every** candidate directory. The one containing the deployed SHA is the source of
truth; the rest are decoys and get neutralized first. A stale repo with authoritative
language is more dangerous than no docs at all.

## 3 — Measure the context tax

```bash
for f in <every file marked "read first" / "mandatory" / "canonical">; do
  echo "$(wc -c <"$f") bytes  $(wc -w <"$f") words  $f"
done
```

Sum it. **Divide bytes by 4 for a rough token count.** **>100k tokens:** exceeds usable
context — the agent is silently reading a random subset; this outranks everything else,
report it first. **>30k:** rules compete with the task. **<15k:** healthy.

Follow every "read X first" pointer transitively. A 400-word CLAUDE.md pointing at a 280 KB
file **is** a 280 KB CLAUDE.md.

## 4 — Verify every architectural claim

For each LOCKED / NON-NEGOTIABLE claim, find the artifact that proves or refutes it:

| Claim type | Evidence, not testimony |
|---|---|
| Infrastructure | `grep -rn '^resource "' **/*.tf` — declared resources only |
| SDK / provider | `package.json` deps **and** actual `new X(...)` call sites |
| "Service X does Y" | Read the function body. Comments lie; `// K8s wrapper` on a function with no K8s is a real failure mode |
| Deployed / complete | Fetch the endpoint. Read `git log`. Never trust a ✅ |
| File path references | `ls` it. Version drift (`-v3` vs `-v4`) is constant |
| Open action items | Check the date. Anything > 30 days old is dead — move it to an issue tracker |

## 5 — Find the conflicts (priority order)

1. **Self-contradiction in one file** — X and not-X. Check lines far apart; drift
   accumulates at the edges.
2. **Cross-file contradiction** — CLAUDE.md vs .cursor/rules.md vs .anti-gravity/rules.md,
   both marked LOCKED.
3. **Competing entry points** — more than one file claiming "read this first," in different
   orders. Count them, hook-injected instructions included.
4. **Ask-vs-act tension** — "stop and ask" beside "use your judgment / speed matters," no
   tiebreaker. The classic cause of "the model didn't warn me before building the wrong thing."
5. **Halt landmines** — absolutes like *"if you are not in <IDE>, stop and say so."* Headless
   agents, CLI, and Cowork are never in an IDE. This silently halts work.

## 6 — Status vs rules

Sort every doc into one tier; mixing tiers is the root cause of bloat. **Tier 1 Rules** —
monthly churn, always loaded, cap 15 KB total. **Tier 2 State** — per-session, current only,
cap 5 KB each, hard-truncate (history goes to session snapshots). **Tier 3 Reference** —
never auto-loaded. Append-only status files inside Tier 1 are the most common failure; flag
any Tier-2 over cap.

## Output — `INSTRUCTION-AUDIT.md`

**Lead with the single highest-impact finding** — if the read tax exceeds context, that is
finding #1 and the rest is secondary. Every finding: its evidence plus a **fix** sized in
minutes or sessions. Include a **"do not touch"** section naming what's genuinely good (an
audit that only criticizes gets ignored). End with **the question the operator didn't ask** —
the structural issue behind the symptom. `##`/`###` headers, bold the decision/number/
filename, tables over paragraphs, no walls.

Order fixes by **(impact ÷ effort)**, not severity. Archiving a decoy repo takes 10 minutes
and removes an agent that actively fights the operator — that beats a 3-hour doc restructure.

**Do not rewrite files unattended.** Deliver the audit plus proposed replacements; the
operator approves. Exception: neutralizing a confirmed decoy repo is always safe — add a
`CLAUDE.md` stub reading *"DEAD MIRROR. Superseded by <real path>. Do not use as guidance."*

Durable fix: an owner + expiry header on every Tier 1–2 doc, and a check that fails when a
doc is over cap or past review. Enforcement at the border beats asking the model to behave.

```
<!-- OWNER: <name> · TIER: 1 · MAX: 15KB · REVIEW: YYYY-MM-DD -->
```
