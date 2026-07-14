---
name: "tigerclaw-daily-checks"
description: "Run Brent's Tiger Claw daily operational health checks end-to-end and report one clear verdict. Use whenever Brent says \"run daily checks\", \"daily checks\", \"run the daily check\", \"is everything healthy\", \"check the system\", \"are we green\", \"is Tiger up\", or at the start of a working session before any Tiger Claw product/proof work. The operator should NEVER have to open the repo or remember which checks to run \u2014 this skill does the whole procedure (automated pass + live probes: prod health, admin status, Mine health + pollution, the unleased lead-pool, latest deploy) and returns a short scannable GO / ISSUES verdict."
---

# Tiger Claw — Daily Checks

Brent's one-word health check. He says "run daily checks" and gets back a short
verdict — never has to go into the repo or remember the procedure. This skill IS
that procedure. Run everything, then report.

Canonical source: `/Users/brentbryson/tiger-claw-v4-core/DAILY_CHECKS.md` (this
skill automates it; if that file and this skill ever disagree, the repo file
wins — re-read it and update this skill).

## Operating rules
- **Report and flag — do NOT auto-fix.** If a check fails, say so plainly and
  point at the cause; let Brent decide. (Exception: if he explicitly says "fix
  it" after seeing the verdict.)
- **Know the false alarms.** Several "failures" are documented noise, not real
  outages (see "Known false alarms" below). Call those out as *likely noise* so
  Brent doesn't panic — but still surface them.
- **Degrade gracefully on auth.** The deeper checks need gcloud + the read
  replica. If gcloud's token has expired, run everything that doesn't need it,
  and tell Brent to run `! gcloud auth login` to unlock the rest — don't silently
  skip.
- **Timestamps in UTC.** Record the exact UTC time of live probes.
- **One eye — keep the output short and scannable.** Top-line verdict, one line
  per check, plain English on failures, no raw logs unless asked.

## Procedure

Run these in order. Setup first:

```bash
export ADMIN_TOKEN="$(cat ~/.tigerclaw-admin-token)"   # required for /admin/*
REPO=/Users/brentbryson/tiger-claw-v4-core
API=https://api.tigerclaw.io
date -u +"%Y-%m-%dT%H:%M:%SZ"                            # stamp the run
```

### 1. Automated pass (the backbone)
```bash
cd "$REPO/api" && ADMIN_TOKEN="$ADMIN_TOKEN" npm run daily:checks
```
Emits PASS/FAIL/WARN for: `front_door`, `public_health`, `admin_status`,
`commerce_unsigned_webhook`, `docs_check`. `human_fire_judgment` is **always**
WARN (manual-only) — that's expected, not a failure. `admin_status` prints the
verdict (want `GO`), deps, mine, incidents, staleHeartbeats, brokenTenants.

### 2. Live prod health
```bash
curl -s --max-time 12 "$API/health" | python3 -c "import sys,json;d=json.load(sys.stdin);print('status',d.get('status'),'gitSha',d.get('build',{}).get('gitSha','')[:12],d.get('checks',{}))"
```
Want `status: ok`, postgres/redis/disk/workers all `ok`. Note the gitSha (the
deployed commit).

### 3. Latest deploy landed
```bash
cd "$REPO" && gh run list --workflow "Deploy to Cloud Run" --limit 3 --json headSha,status,conclusion,createdAt --jq '.[] | "\(.headSha[0:12]) \(.status) \(.conclusion)"'
```
Newest should be `completed success`. An `in_progress` is fine (mid-deploy). A
`failure` matters — but the Cloud Build step OOMs intermittently (see false
alarms); a re-run usually clears it.

### 4. Mine health + pollution
```bash
curl -s --max-time 15 -H "Authorization: Bearer $ADMIN_TOKEN" "$API/admin/pipeline/health" | python3 -c "import sys,json;d=json.load(sys.stdin);print('totalFacts',d.get('totalFacts'),'last24h',d.get('factsLast24h'),'newest',d.get('newestFact'))"
cd "$REPO/api" && npx tsx src/scripts/mine-health-check.ts   # read-only pollution check
```
Want: recent `newestFact` (mine ran in the last day), non-zero `factsLast24h`,
**fiction-leak rate 0%**, no unclassified subreddits. Sample a couple of recent
Network Marketer facts and gut-check they read like real in-transition prospects,
not spam.

### 5. Lead supply — are leads actually available to flow? (needs gcloud)
This is the check that catches "Brent gets no leads" before he notices. Start the
read replica proxy, then count the **unleased fresh** Network Marketer pool.
```bash
PROJECT=hybrid-matrix-472500-k5
REPLICA=hybrid-matrix-472500-k5:us-central1:tiger-claw-postgres-replica
(cloud-sql-proxy --port 5433 "$REPLICA" >/tmp/csqlproxy.log 2>&1 &); sleep 7
DBURL=$(gcloud secrets versions access latest --secret=tiger-claw-database-url --project="$PROJECT")
USER=$(echo "$DBURL" | sed -E 's|^postgres(ql)?://([^:]+):.*|\2|')
export PGPASSWORD=$(echo "$DBURL" | sed -E 's|^postgres(ql)?://[^:]+:([^@]+)@.*|\2|')
psql -h 127.0.0.1 -p 5433 -U "$USER" -d tiger_claw_shared -P pager=off -tAc "
SELECT count(*) FROM market_intelligence mi
WHERE mi.domain='Network Marketer' AND mi.archived_at IS NULL
  AND mi.created_at >= now()-interval '30 days'
  AND COALESCE(mi.entity_id,mi.source_url) IS NOT NULL
  AND NOT EXISTS (SELECT 1 FROM mine_fact_leases l JOIN market_intelligence m2 ON m2.id=l.fact_id
        WHERE COALESCE(m2.entity_id,m2.source_url)=COALESCE(mi.entity_id,mi.source_url));"
pkill -f "cloud-sql-proxy --port 5433"
```
If this is **0**, the pool is locked and no operator's scout will surface
anything — flag it loud (that's the bug that silently starved the operator). If
gcloud is expired (`Reauthentication failed`), skip this one and tell Brent to
run `! gcloud auth login`, then it can be re-run.

## Known false alarms (flag as *likely noise*, don't panic)
- **`docs_check` FAIL** — usually living-doc drift (a PR# referenced as merged
  that was actually closed, or a stale "Last updated" timestamp), not a product
  problem. Reconcilable in a docs PR.
- **`/admin/status` DEGRADED with a stale incident** — an already-fixed bug whose
  `admin_exceptions` row was never acknowledged keeps the verdict yellow (~5 min
  cache). Check whether the incident's endpoint already passes again.
- **Scanner-shaped incidents** — `MISSING_SESSION_TOKEN` / `INVALID_SESSION_TOKEN`
  on `/.env`, `/phpinfo`, leading-underscore slugs (`_synthmon_prod`) are
  scanner/probe noise, classified `info` — not real failures.
- **Cold-sweep false-RED** — a single-shot probe catching a transient Google 503 /
  slow PG can read DOWN; the confirm-retry layer rescues it. A green re-probe
  means it was a flap.
- **Deploy `failure` = Cloud Build heap OOM** — intermittent; a re-run of the
  "Deploy to Cloud Run" job usually goes green.

## Output format (what Brent sees)
Lead with the verdict, then one line per check. Example:

```
✅ ALL GOOD — 2026-06-16T18:41Z

front_door         ok
public_health      ok (pg/redis/workers)
admin_status       GO · 0 broken tenants · 12 incidents (all scanner/stale — noise)
commerce_webhook   ok (unsigned rejected)
docs_check         ok
prod /health       ok · gitSha ccfff8fc
latest deploy      success
mine               ok · 55 facts/24h · 0% pollution
lead pool          469 fresh unleased — flowing
```

When something's wrong, replace ALL GOOD with `⚠️ N ISSUES`, put the failing
lines first, and add one plain-English line per issue: what broke, where to look,
and whether it's a known false alarm. No raw logs unless Brent asks.

## Codex Runtime

Never expose or print secret, credential, or token values.

Mandatory dependencies:
- `tiger-claw-v4-core repository`
- `gcloud and database credentials`

Preflight each dependency using MCP/app capability discovery, CLI availability/version checks, read-only filesystem or Git checks for repositories, and provider auth-status commands without printing secrets, credentials, or tokens.
If any mandatory dependency is unavailable, stop and report a concise blocked state naming the missing dependency and the next action needed.
