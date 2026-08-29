---
name: optimize
description: Audit and optimize the instruction layer an AI agent actually reads — CLAUDE.md, AGENTS.md, .cursor/rules.md, .anti-gravity/rules.md, hooks, settings, and every doc marked "read first." Measures the real context tax, finds contradictions, and verifies every architectural claim against ground truth (code, terraform, git, live endpoints) instead of trusting the documents. Use when Brent says "optimize", "audit my instructions", "is my CLAUDE.md holding you back", "why is the agent ignoring my rules", "find misaligned instructions", or after any incident where an agent followed a stale rule.
---

# /optimize — Instruction Layer Auditor

## Prime rule

**Documents are testimony. Code, terraform, git and live endpoints are evidence.**

Never validate an instruction file against another instruction file. Every architectural claim gets checked against a running artifact. A doc that says "we use GKE" proves nothing; `grep google_container_cluster` in terraform proves something.

---

## Phase 1 — Inventory (find every authority)

Locate all files that claim to govern agent behavior. Do not stop at the obvious one.

```bash
find . -maxdepth 4 \( -iname "CLAUDE.md" -o -iname "AGENTS.md" -o -iname "rules.md" \
  -o -iname "*.mdc" -o -iname "START_HERE.md" -o -iname "SOTU.md" \
  -o -iname "BIG-PICTURE.md" -o -iname "NEXT_SESSION.md" \) \
  -not -path "*/node_modules/*"
cat .claude/settings.json ~/.claude/settings.json 2>/dev/null   # hooks inject instructions too
ls ~/ | grep -i <project>                                        # sibling/stale checkouts
```

**Sibling checkouts are the #1 source of poisoned instructions.** If the project has more than one directory, determine which is real before auditing anything (Phase 2).

## Phase 2 — Ground truth (which repo is real?)

```bash
curl -s <prod-health-endpoint>          # or WebFetch — get the deployed gitSha
git cat-file -t <deployed-sha>          # "bad object" => THIS IS NOT THE REAL REPO
git branch -a --contains <deployed-sha>
```

Run this in **every** candidate directory. The one containing the deployed SHA is the source of truth. All others are decoys and must be neutralized before anything else — a stale repo with authoritative language is more dangerous than no docs at all.

## Phase 3 — Measure the context tax

```bash
for f in <every file marked "read first" / "mandatory" / "canonical">; do
  echo "$(wc -c <"$f") bytes  $(wc -w <"$f") words  $f"
done
```

Sum it. **Divide bytes by 4 for a rough token count.**

- **> 100k tokens:** exceeds usable context. The agent is silently reading a random subset. This finding outranks everything else — report it first.
- **> 30k tokens:** significant degradation; rules compete with the task.
- **< 15k tokens:** healthy.

Follow every "read X first" pointer transitively. A 400-word CLAUDE.md that points at a 280 KB file is a 280 KB CLAUDE.md.

## Phase 4 — Verify every architectural claim

For each LOCKED / NON-NEGOTIABLE claim, find the artifact that proves or refutes it:

| Claim type | Evidence, not testimony |
|---|---|
| Infrastructure | `grep -rn '^resource "' **/*.tf` — declared resources only |
| SDK / provider | `package.json` deps **and** actual `new X(...)` call sites |
| "Service X does Y" | Read the function body. Comments lie; `// K8s wrapper` on a function with no K8s is a real failure mode |
| Deployed / complete | Fetch the endpoint. Read `git log`. Never trust a ✅ |
| File path references | `ls` it. Version drift (`-v3` vs `-v4`) is constant |
| Open action items | Check the date. Anything > 30 days old is dead and must move to an issue tracker |

## Phase 5 — Find the conflicts

Look specifically for these five, in priority order:

1. **Self-contradiction inside one file** — the same doc asserting X and not-X (check line numbers far apart; drift accumulates at the edges).
2. **Cross-file contradiction** — CLAUDE.md vs .cursor/rules.md vs .anti-gravity/rules.md, both marked LOCKED.
3. **Competing entry points** — more than one file claiming "read this first," with different orders. Count them. Include hook-injected instructions.
4. **Ask-vs-act tension** — a rule saying "stop and ask" alongside one saying "use your judgment / speed matters," with no tiebreaker. This is the classic cause of "the model didn't warn me before building the wrong thing."
5. **Halt landmines** — any absolute like *"if you are not in <IDE>, stop and say so."* Headless agents, CLI, and Cowork are never in an IDE. This silently halts work.

## Phase 6 — Status vs rules

Sort every doc into one tier. Mixing tiers is the root cause of bloat:

- **Tier 1 — Rules.** Changes monthly. Always loaded. Cap 15 KB total.
- **Tier 2 — State.** Changes per session. Current only. Cap 5 KB each, hard-truncate; history goes to session snapshots.
- **Tier 3 — Reference.** Never auto-loaded. Read only when the task names it.

Append-only status files inside Tier 1 are the most common failure. Flag any Tier-2 file over cap.

---

## Output

Write `INSTRUCTION-AUDIT.md`. Rules for it:

- **Lead with the single highest-impact finding.** If the read tax exceeds context, that is finding #1 and everything else is secondary.
- Every finding carries **evidence** — the command run and what it returned. No claim without an artifact.
- Every finding carries a **fix**, sized in minutes or sessions.
- Include a **"do not touch"** section. Say what's genuinely good. An audit that only criticizes gets ignored.
- End with **the question the operator didn't ask** — the structural issue behind the symptom.
- Headers `##`/`###`, bold the decision/number/filename, tables over paragraphs. No walls of text.

## Then propose

Order fixes by **(impact ÷ effort)**, not by severity. Archiving a decoy repo takes 10 minutes and removes an agent that actively fights the operator — that beats a 3-hour doc restructure every time.

Do not rewrite files unattended. Deliver the audit plus proposed replacements, and let the operator approve. Exception: neutralizing a confirmed decoy repo is always safe — add a `CLAUDE.md` stub reading *"DEAD MIRROR. Superseded by <real path>. Do not use as guidance."*

## Durable fix

Recommend an owner + expiry header on every Tier 1–2 doc, and a check that fails when a doc is over cap or past review:

```
<!-- OWNER: <name> · TIER: 1 · MAX: 15KB · REVIEW: YYYY-MM-DD -->
```

Enforcement at the border beats asking the model to behave. Docs should be governed the same way code is.
