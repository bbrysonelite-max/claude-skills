---
name: jumbo-health
description: On-demand health check of Brent's Jumbo memory system (containers, bridge, gateway, capture, backups, scheduled jobs, recall) ending in ONE loud GO / RED verdict with receipts. Use when Brent says "jumbo health", "check jumbo", "is jumbo up", "is my memory healthy", "memory health check", before relying on Jumbo in a new session, or after any machine restart / docker event / Anthropic outage. Read-only — never repairs, restarts, or deletes anything.
---

# jumbo-health

One command tells the truth about the whole memory system. Fail LOUD: a RED
names every failed check; there is no quiet degraded state. Everything here is
READ-ONLY — if a fix seems needed, report it and ask Brent; never touch
anything named `tdai-memory*`, its volume, or the bridge process
(law: `~/.config/brent-dev-memory/PROTECTED.json`).

## Step 1 — the core six (one script, already the daily engine)

```bash
bash /Users/brentbryson/brent-dev-memory-bridge/scripts/daily-memory-check.sh
```

Prints exactly one line: `MEMORY-CHECK GREEN <utc>` or
`MEMORY-CHECK RED <utc> — <failed,check,names>` (details on stderr).
Covers: both containers `(healthy)` · bridge `:8765` ok · gateway `:8420`
answering with auth · capture < 26h fresh · core backup < 26h fresh + non-empty.
Exit 1 = RED. If the script itself is missing, that IS a RED — say so.

## Step 2 — the scheduled-jobs lane (rot detection)

```bash
launchctl list | grep -E "io.brent.(memory-backup|memory-check|memory-sweep|dev-memory-bridge)"
```

Expect all four rows, exit status 0 each. A missing row or nonzero status =
RED item. Then log freshness (staleness = the job silently stopped firing):

```bash
tail -1 ~/Library/Logs/memory-check.log     # expect GREEN line < 26h old
tail -3 ~/Library/Logs/memory-sweep.log     # newest weekly-sweep block < 8d old, "ok: exit 0"
ls -t ~/MEMORY-BACKUP/tdai-memory-core-data-*.tar.gz | head -1   # < 26h old
```

## Step 3 — live recall probe (the point of the whole system)

Search via MCP `memory_search` (query: something recent, e.g. "sweep lane")
— expect scored hits. No hits on a query that should hit = RED item, likely
index/bridge trouble; check `RECALL-LADDER-HANDOFF.md` before proposing anything.

## Step 4 — verdict, one block, receipts

```
JUMBO HEALTH: GO <utc>            (or: RED <utc> — <n> failures)
  core-six    GREEN|RED(<names>)  <utc>
  jobs        4/4 loaded          | missing: <names>
  logs        check <age> · sweep <age> · backup <age>
  recall      <n> hits, top <score>
```

Every line carries its command's real output — never summarize a check you
did not run this minute. Health verdicts come from live commands only —
Jumbo answers history and context (and beats any guess); the checks above
answer "now".

## RED protocol

1. Name every failed check (the scripts already do — relay, don't soften).
2. Do NOT repair autonomously. Diagnosis is fine (read logs, `docker ps`,
   curl again); any restart/bootstrap/rm needs Brent's explicit GO.
3. If memory-guard blocks a diagnostic command, ask Brent — never work around.
4. Capture a durable RED finding to Jumbo via `memory_capture` only after
   Brent has seen it.

## Related

- Weekly sweep PROPOSALS review: `state/sweep-proposals/PROPOSALS.md` — apply
  only on Brent's GO via `memory_supersede` (propose-only law, sweep/SPEC.md).
- Backup/restore runbook receipts: restore is extract-to-scratch; full volume
  restore requires container stop = Brent's order only.
