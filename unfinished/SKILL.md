---
name: unfinished
description: Enumerates every work item that remains UNFINISHED (started, not done), UNVERIFIED (claimed, no receipt), or UNCONFIRMED (awaiting Brent's eyes or word) — swept from ground truth, never from memory alone. Use when Brent says "unskill", "what remains", "what's left", "what's unfinished/unverified/unconfirmed", "open debts", or at session close before a handoff.
---

# The Unfinished Skill

Every skill ships work. This one ships the SHADOW of the work: the honest list of
what is NOT done, NOT proven, and NOT ratified. It exists because finished work
announces itself with receipts, while unfinished work hides in silence — and
silence is where a 10-minute fix becomes a 4-hour one.

## The three buckets (exact definitions — sort every item into exactly one)

| Bucket | Test | Example |
|---|---|---|
| **UNFINISHED** | Work started, end state not reached | branch open, PR unmerged, TODO filed, slice mid-flight |
| **UNVERIFIED** | Completion CLAIMED, but no command+output+UTC receipt read back from the artifact | "deployed" with no endpoint fetch; agent-reported result never disk-diffed |
| **UNCONFIRMED** | Done and receipted, but the gate is HIS — merge, GO, walk, ruling, or eyes not yet given | PR green awaiting his merge; walk procedure written, his paste not received |

A claim with a receipt is DONE — it does not appear. Absence is a measurement:
an empty bucket is stated as "swept N sources, bucket empty", never omitted.

## The sweep (run ALL, each is a live query — counts from memory are FORBIDDEN)

1. **This session's own tail.** Reread the current conversation for the words
   UNVERIFIED, owed, pending, in flight, "will", "after this". Anything you
   yourself labeled UNVERIFIED and never closed goes in bucket 2.
2. **Memory index.** `grep -n -iE 'owed|debt|UNVERIFIED|open|pending|HIS call|🔴' ~/.claude/projects/-Users-brentbryson/memory/MEMORY.md`
   — then open only the files whose hook line still looks live. Memory says what
   WAS true: anything actionable gets re-verified live before listing (a stale
   "owed" that's since shipped is a candidate supersede, list it as such).
3. **Repos.** For each active repo (bridge, tiger v4-core, others named this
   session): `gh pr list --state open` · `git status --porcelain` (untracked/
   uncommitted) · `git log origin/main..HEAD` on any local branch.
4. **Jumbo.** POST /load-context (or memory_search) for "owed OR debt OR
   unverified OR pending" scoped to the active projects. Bridge down = say so
   loudly and mark the sweep PARTIAL — never silently skip a source.
5. **Live flags.** Logs that hold un-adjudicated events: credential-gate
   SUPPRESS lines, memory-load FAIL lines since last review, daily-check REDs.

## Output format (a board, not prose)

```
# UNSKILL BOARD — <UTC of sweep>   sources swept: N of M (name any missed)

## UNCONFIRMED — HIS move (list first: these block, cheapest to clear)
- [what] · gate: [merge/GO/walk/ruling] · receipt trail: [where] · ask: [one plain yes/no]

## UNFINISHED — someone's move
- [what] · whose: [mine / lane-X / HIS] · next concrete action · where recorded

## UNVERIFIED — claims needing receipts
- [claim] · claimed by: [who/when] · the verify command to run

## Bucket empty: [name buckets that are empty, with sources-swept receipt]
```

Rules: every line carries where it is RECORDED (file/PR/log) — an unfinished
item that lives nowhere but this board gets written to memory in the same
breath (no broken windows). One HIS-decision per ask, dead simple. Order
UNCONFIRMED first — clearing his queue unblocks the most for the least.

## What this skill never does

- Never fixes anything mid-sweep (flag, don't fix).
- Never states "nothing open" without naming the sources swept and their UTC.
- Never lists a rumor: an item someone mentioned but no artifact records is
  listed as "hearsay — needs grounding", not as fact.
- Never counts closed-by-his-ruling items (⚰️) as open — a ruling IS an end state.
