#!/usr/bin/env bash
# ship-it — TigerClaw merge → CI-watch → Cloud Run deploy → live /health(SHA) loop.
# Encodes Brent's rules: never push to main, verify MERGED, inspect the MERGED sha's
# deploy (not just PR-head rollup), verify live /health gitSha matches, timestamp UTC.
# The ONLY mutating action is `merge`, and it refuses to run without --confirm.
set -uo pipefail

HEALTH_URL="${SHIP_IT_HEALTH_URL:-https://api.tigerclaw.io/health}"
DEPLOY_WORKFLOW="${SHIP_IT_DEPLOY_WORKFLOW:-deploy.yml}"
REPO_DIR="${SHIP_IT_REPO_DIR:-$HOME/tiger-claw-v4-core}"
MERGE_METHOD="${SHIP_IT_MERGE_METHOD:-squash}"
POLL_TRIES="${SHIP_IT_POLL_TRIES:-24}"
POLL_SLEEP="${SHIP_IT_POLL_SLEEP:-15}"
SHA_FILE="/tmp/ship-it-last-sha"

ts(){ date -u +"%Y-%m-%dT%H:%M:%SZ"; }
say(){ printf '%s\n' "$*"; }
jget(){ python3 -c "import sys,json
try: print(json.load(sys.stdin)$1)
except Exception: pass" 2>/dev/null; }

cd "$REPO_DIR" 2>/dev/null || { say "ERROR: repo not found at $REPO_DIR (set SHIP_IT_REPO_DIR)"; exit 1; }

checks(){ # read-only: poll CI to completion, return its verdict
  local pr="$1"
  say "[$(ts)] CI checks for PR #$pr (watching until complete)…"
  gh pr checks "$pr" --watch --interval "$POLL_SLEEP" >/dev/null 2>&1 || true
  gh pr checks "$pr"
}

do_merge(){ # MUTATING: only with --confirm; verify MERGED; capture merge sha
  local pr="$1" confirm="${2:-}"
  if [ "$confirm" != "--confirm" ]; then
    say "REFUSING to merge PR #$pr without explicit approval."
    say "Per-PR rule: re-run  ship-it.sh merge $pr --confirm"; exit 2
  fi
  if ! gh pr checks "$pr" >/dev/null 2>&1; then
    say "[$(ts)] CI is NOT green on PR #$pr — aborting merge."; exit 3
  fi
  say "[$(ts)] Merging PR #$pr (--$MERGE_METHOD, delete branch)…"
  gh pr merge "$pr" "--$MERGE_METHOD" --delete-branch || { say "merge command failed"; exit 4; }
  local state mergesha
  state="$(gh pr view "$pr" --json state -q .state 2>/dev/null)"
  mergesha="$(gh pr view "$pr" --json mergeCommit -q .mergeCommit.oid 2>/dev/null)"
  say "[$(ts)] PR #$pr state=$state mergeSHA=$mergesha"
  [ "$state" = "MERGED" ] || { say "STATE IS NOT MERGED — STOP. Closeout is INCOMPLETE."; exit 5; }
  printf '%s' "$mergesha" > "$SHA_FILE"
  say "[$(ts)] Merge verified. Now run:  ship-it.sh deploy"
}

deploy(){ # read-only: watch THIS merge's deploy run (matched by SHA), then poll /health until gitSha==expected & ok
  local expected="${1:-$(cat "$SHA_FILE" 2>/dev/null)}"
  local runid=""
  if [ -n "$expected" ]; then
    say "[$(ts)] Locating $DEPLOY_WORKFLOW run for merged SHA $expected ..."
    runid="$(gh run list --workflow="$DEPLOY_WORKFLOW" --branch main -L 30 --json databaseId,headSha -q '.[] | [.headSha, (.databaseId|tostring)] | @tsv' 2>/dev/null | awk -v s="$expected" '$1==s{print $2; exit}')"
  else
    say "[$(ts)] WARNING: no expected SHA (run 'merge' first or pass one) — the SHA will NOT be verified."
    runid="$(gh run list --workflow="$DEPLOY_WORKFLOW" --branch main -L 1 --json databaseId -q '.[0].databaseId' 2>/dev/null)"
  fi
  if [ -n "$runid" ]; then
    gh run watch "$runid" --exit-status >/dev/null 2>&1 \
      && say "[$(ts)] deploy run $runid (SHA-matched): success" \
      || say "[$(ts)] WARNING: deploy run $runid did not succeed — PARTIAL until /health proves otherwise"
  elif [ -n "$expected" ]; then
    say "[$(ts)] no deploy run for $expected yet — verifying via /health poll only (will NOT trust a stale 'latest' run)"
  else
    say "[$(ts)] (no $DEPLOY_WORKFLOW run found; verifying via /health directly)"
  fi
  say "[$(ts)] Polling $HEALTH_URL for live SHA (want: ${expected:-any})…"
  local i body live status
  for i in $(seq 1 "$POLL_TRIES"); do
    body="$(curl -fsS --max-time 10 "$HEALTH_URL" 2>/dev/null)"
    live="$(printf '%s' "$body" | jget '["build"]["gitSha"]')"
    status="$(printf '%s' "$body" | jget '["status"]')"
    if [ -n "$expected" ]; then
      if [ "$live" = "$expected" ] && [ "$status" = "ok" ]; then
        say "[$(ts)] LIVE ✅  gitSha=$live  status=ok  ($HEALTH_URL)"; return 0
      fi
    elif [ "$status" = "ok" ] && [ -n "$live" ]; then
      say "[$(ts)] health ok but SHA UNVERIFIED ⚠️  liveSha=$live (could be a prior revision — pass the merged SHA to confirm)"; return 0
    fi
    say "  attempt $i/$POLL_TRIES: live=${live:-?} status=${status:-?} — wait ${POLL_SLEEP}s"
    sleep "$POLL_SLEEP"
  done
  say "[$(ts)] TIMEOUT: live /health never reached gitSha=$expected & status=ok — PARTIAL. See docs/ROLLBACK.md."
  return 6
}

case "${1:-}" in
  checks) shift; checks "$@";;
  merge)  shift; do_merge "$@";;
  deploy) shift; deploy "$@";;
  full)
    shift; pr="${1:-}"; confirm="${2:-}"
    [ -n "$pr" ] || { say "usage: ship-it.sh full <pr> [--confirm]"; exit 1; }
    checks "$pr"
    if [ "$confirm" = "--confirm" ]; then do_merge "$pr" --confirm && deploy
    else say "[$(ts)] CI shown above. Get Brent's explicit OK, then: ship-it.sh merge $pr --confirm && ship-it.sh deploy"; fi
    ;;
  *) say "usage: ship-it.sh {checks <pr> | merge <pr> --confirm | deploy [sha] | full <pr> [--confirm]}"; exit 1;;
esac
