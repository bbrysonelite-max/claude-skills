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
# SHA_FILE deleted 2026-07-20 (G1): a cached SHA in /tmp caused a false "LIVE ✅"
# for the PREVIOUS merge on #1460. deploy now resolves from the PR every time.

# G3-mirror (2026-07-20): a PR that self-describes as unmergeable cannot be merged
# by this tool. Same regexes as .github/workflows/merge-hygiene.yml — keep in sync.
PR_HYGIENE_TITLE='DO NOT MERGE|WIP'
PR_HYGIENE_BODY='review pending'

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

hygiene_check(){ # exits 7 with reason if the PR itself says "don't merge me"
  local pr="$1" title body
  title="$(gh pr view "$pr" --json title -q .title 2>/dev/null)"
  body="$(gh pr view "$pr" --json body -q .body 2>/dev/null)"
  if printf '%s' "$title" | grep -qiE "$PR_HYGIENE_TITLE"; then
    say "[$(ts)] HYGIENE BLOCK: title matches /$PR_HYGIENE_TITLE/i — \"$title\""; exit 7; fi
  if printf '%s' "$body" | grep -qiE "$PR_HYGIENE_BODY"; then
    say "[$(ts)] HYGIENE BLOCK: body matches /$PR_HYGIENE_BODY/i (e.g. 'Review pending')"; exit 7; fi
}

do_merge(){ # MUTATING: only with --confirm; MERGED-state is the ONLY success signal
  local pr="$1" confirm="${2:-}"
  if [ "$confirm" != "--confirm" ]; then
    say "REFUSING to merge PR #$pr without explicit approval."
    say "Per-PR rule: re-run  ship-it.sh merge $pr --confirm"; exit 2
  fi
  hygiene_check "$pr"
  if ! gh pr checks "$pr" >/dev/null 2>&1; then
    say "[$(ts)] CI is NOT green on PR #$pr — aborting merge."; exit 3
  fi
  say "[$(ts)] Merging PR #$pr (--$MERGE_METHOD, delete branch)…"
  # Cleanup failure (e.g. a worktree holds the branch) must NOT mask a successful
  # merge: capture output, don't exit on nonzero — the PR state is the truth.
  # (2026-07-20: exiting here left a STALE cached SHA that deploy then trusted.)
  local mergeout
  mergeout="$(gh pr merge "$pr" "--$MERGE_METHOD" --delete-branch 2>&1)" \
    || say "[$(ts)] note: merge command exit nonzero (may be branch-cleanup only): $mergeout"
  local state mergesha
  state="$(gh pr view "$pr" --json state -q .state 2>/dev/null)"
  mergesha="$(gh pr view "$pr" --json mergeCommit -q .mergeCommit.oid 2>/dev/null)"
  say "[$(ts)] PR #$pr state=$state mergeSHA=$mergesha"
  [ "$state" = "MERGED" ] || { say "STATE IS NOT MERGED — STOP. Closeout is INCOMPLETE."; exit 5; }
  say "[$(ts)] Merge verified. Now run:  ship-it.sh deploy $pr"
}

deploy(){ # read-only. deploy <pr#|sha>. GO only on the FULL proven chain (G1+G2); ledger line on GO (G4).
  local target="${1:-}"
  [ -n "$target" ] || { say "usage: ship-it.sh deploy <pr#|sha> — a cached SHA is never trusted"; exit 8; }
  local pr="" expected=""
  if printf '%s' "$target" | grep -qE '^[0-9]+$'; then
    pr="$target"
    local state; state="$(gh pr view "$pr" --json state -q .state 2>/dev/null)"
    [ "$state" = "MERGED" ] || { say "[$(ts)] PARTIAL — PR #$pr state=${state:-unknown} (not MERGED)"; return 6; }
    expected="$(gh pr view "$pr" --json mergeCommit -q .mergeCommit.oid 2>/dev/null)"
    [ -n "$expected" ] || { say "[$(ts)] PARTIAL — cannot resolve mergeCommit for #$pr"; return 6; }
    say "[$(ts)] PR #$pr mergeCommit=$expected (resolved fresh from GitHub — never cached)"
  elif printf '%s' "$target" | grep -qE '^[0-9a-f]{40}$'; then
    expected="$target"; say "[$(ts)] SHA mode: $expected (no PR context — migration check skipped, ledger skipped)"
  else
    say "usage: ship-it.sh deploy <pr#|40-hex-sha>"; exit 8
  fi
  # 1) the deploy RUN for THIS sha — wait for it to exist; never match an older run
  local runid="" i
  for i in $(seq 1 "$POLL_TRIES"); do
    runid="$(gh run list --workflow="$DEPLOY_WORKFLOW" --branch main -L 50 --json databaseId,headSha \
      -q '.[] | [.headSha, (.databaseId|tostring)] | @tsv' 2>/dev/null | awk -v s="$expected" '$1==s{print $2; exit}')"
    [ -n "$runid" ] && break
    say "  waiting for $DEPLOY_WORKFLOW run for $expected ($i/$POLL_TRIES)…"; sleep "$POLL_SLEEP"
  done
  [ -n "$runid" ] || { say "[$(ts)] PARTIAL — no $DEPLOY_WORKFLOW run for $expected appeared"; return 6; }
  gh run watch "$runid" --exit-status >/dev/null 2>&1 \
    || { say "[$(ts)] PARTIAL — deploy run $runid did not succeed"; return 6; }
  say "[$(ts)] deploy run $runid: success (headSha == mergeCommit)"
  # 2) live /health must serve THIS sha
  local body live status ok=""
  for i in $(seq 1 "$POLL_TRIES"); do
    body="$(curl -fsS --max-time 10 "$HEALTH_URL" 2>/dev/null)"
    live="$(printf '%s' "$body" | jget '["build"]["gitSha"]')"
    status="$(printf '%s' "$body" | jget '["status"]')"
    [ "$live" = "$expected" ] && [ "$status" = "ok" ] && { ok=1; break; }
    say "  attempt $i/$POLL_TRIES: live=${live:-?} status=${status:-?} — wait ${POLL_SLEEP}s"
    sleep "$POLL_SLEEP"
  done
  [ -n "$ok" ] || { say "[$(ts)] PARTIAL — /health never served gitSha=$expected & ok. See docs/ROLLBACK.md."; return 6; }
  say "[$(ts)] /health: gitSha=$live status=ok"
  # 3) migration proof (PR mode only): every migration in the diff must appear applied in prod logs
  local migs="" m found
  if [ -n "$pr" ]; then
    migs="$(gh pr diff "$pr" --name-only 2>/dev/null | grep -E '^api/migrations/.*\.sql$' | grep -v '_down\.sql$' || true)"
    for m in $migs; do
      m="$(basename "$m")"
      found="$(gcloud logging read \
        "resource.type=\"cloud_run_revision\" AND textPayload:\"Successfully applied $m\"" \
        --limit=1 --freshness=2h --format='value(textPayload)' 2>/dev/null)"
      [ -n "$found" ] || { say "[$(ts)] PARTIAL — migration $m NOT observed applied in prod logs (freshness 2h)"; return 6; }
      say "[$(ts)] migration proof: $found"
    done
  fi
  # 4) verdict + ledger (G4): GO means deployed-and-proven; the WALK is still owed.
  say "[$(ts)] GO ✅  #${pr:-—}  gitSha=$expected  status=ok  migrations=$(printf '%s' "${migs:-none}" | tr '\n' ' ')  — DEPLOYED-ONLY until a walk record upgrades it"
  if [ -n "$pr" ]; then
    local line="| #$pr | ${expected:0:12} | $(ts) | DEPLOYED-ONLY | run $runid + /health SHA match$( [ -n "$migs" ] && printf ' + migration log' ) |"
    printf '%s\n' "$line" >> "$REPO_DIR/MERGE_LEDGER.md" \
      && say "[$(ts)] ledger: appended to MERGE_LEDGER.md (session docs PR carries it in)"
    gh pr comment "$pr" --body "ship-it ledger: $line" >/dev/null 2>&1 \
      && say "[$(ts)] ledger: posted as PR comment (durable, zero-push)" \
      || say "[$(ts)] WARNING: PR comment failed — ledger exists only locally"
  fi
  return 0
}

case "${1:-}" in
  checks) shift; checks "$@";;
  merge)  shift; do_merge "$@";;
  deploy) shift; deploy "$@";;
  full)
    shift; pr="${1:-}"; confirm="${2:-}"
    [ -n "$pr" ] || { say "usage: ship-it.sh full <pr> [--confirm]"; exit 1; }
    checks "$pr"
    if [ "$confirm" = "--confirm" ]; then do_merge "$pr" --confirm && deploy "$pr"
    else say "[$(ts)] CI shown above. Get Brent's explicit OK, then: ship-it.sh merge $pr --confirm && ship-it.sh deploy $pr"; fi
    ;;
  *) say "usage: ship-it.sh {checks <pr> | merge <pr> --confirm | deploy <pr#|sha> | full <pr> [--confirm]}"; exit 1;;
esac
