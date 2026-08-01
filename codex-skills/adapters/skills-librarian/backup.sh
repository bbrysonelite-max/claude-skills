#!/usr/bin/env bash
# Codex skills-librarian backup: stage an explicit reviewed file allowlist,
# create a topic branch, push it, and open a PR. Never merges without a
# separate per-PR confirmation.
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
SKILLS_DIR="${SKILLS_DIR:-$HOME/.codex/skills}"
CODEX_SKILLS_REPO="${CODEX_SKILLS_REPO:-}"

ts(){ date -u +"%Y-%m-%dT%H:%M:%SZ"; }
stamp(){ date -u +"%Y%m%d-%H%M%S"; }
say(){ printf '%s\n' "$*"; }
refuse(){ say "REFUSING: $*"; exit 2; }

[ -n "$CODEX_SKILLS_REPO" ] || refuse "CODEX_SKILLS_REPO is required."
cd "$CODEX_SKILLS_REPO" 2>/dev/null || refuse \
  "repository not found at CODEX_SKILLS_REPO=$CODEX_SKILLS_REPO"
repo_root="$(git rev-parse --show-toplevel 2>/dev/null)" || refuse \
  "$CODEX_SKILLS_REPO is not a Git repository."
[ "$(pwd -P)" = "$(cd "$repo_root" && pwd -P)" ] || refuse \
  "CODEX_SKILLS_REPO must name the repository root: $repo_root"
git remote get-url origin >/dev/null 2>&1 || refuse \
  "repository has no origin remote."

integrity_gate(){
  say "[$(ts)] Integrity gate (audit.py)…"
  if ! SKILLS_DIR="$SKILLS_DIR" CODEX_SKILLS_REPO="$repo_root" \
    python3 "$SCRIPT_DIR/audit.py" >/dev/null 2>&1; then
    refuse "installed-shelf integrity or mirror freshness check failed."
  fi
  say "  integrity clean."
}

reset_reviewed_paths(){
  if [ "${#backup_paths[@]}" -gt 0 ]; then
    git reset -q -- "${backup_paths[@]}" 2>/dev/null || true
  fi
}

guard_no_symlink_or_gitlink(){
  local staged mode
  while IFS= read -r staged; do
    [ -n "$staged" ] || continue
    if [ -L "$staged" ]; then
      reset_reviewed_paths
      refuse "reviewed path is a symlink: $staged"
    fi
    mode="$(git ls-files --stage -- "$staged" 2>/dev/null | awk 'NR==1 {print $1}')"
    if [ "$mode" = "160000" ]; then
      reset_reviewed_paths
      refuse "reviewed path is a nested Git repository: $staged"
    fi
  done < <(git diff --cached --name-only)
}

guard_exact_staged_allowlist(){
  local staged allowed
  while IFS= read -r staged; do
    [ -n "$staged" ] || continue
    allowed=0
    for reviewed in "${backup_paths[@]}"; do
      if [ "$staged" = "$reviewed" ]; then
        allowed=1
        break
      fi
    done
    if [ "$allowed" -ne 1 ]; then
      reset_reviewed_paths
      refuse "staged path escaped the reviewed allowlist: $staged"
    fi
  done < <(git diff --cached --name-only)
}

secret_scan(){
  say "[$(ts)] Secret-scanning staged diff…"
  local prefix_re generic_re added hits
  prefix_re='(^|[^A-Za-z0-9])(sk-|sk_|blt_|AIza|AKIA|ghp_|xox)[A-Za-z0-9_/+-]{16,}|-----BEGIN[A-Z ]+PRIVATE KEY'
  generic_re='(api[_-]?key|client_secret|[A-Za-z0-9]*_secret|[A-Za-z0-9]*_token|password)[[:space:]"]*[:=][[:space:]"]*("[^"]{6,}|[A-Za-z0-9_/.+-]*[0-9][A-Za-z0-9_/.+-]*)'
  added="$(git diff --cached -U0 | grep -nE '^\+' | grep -vE '^[0-9]+:\+\+\+' || true)"
  hits="$(printf '%s\n' "$added" | grep -iE "$prefix_re|$generic_re" 2>/dev/null || true)"
  if [ -n "$hits" ]; then
    say "STOP: possible secret(s) in the staged diff. Locations only:"
    printf '%s\n' "$hits" |
      sed -E 's/([:=]).*/\1 <redacted>/' |
      cut -c1-80 |
      head -40
    reset_reviewed_paths
    exit 4
  fi
  say "  secret scan clean."
}

if [ "${1:-}" = "merge" ]; then
  pr="${2:-}"
  merge_confirm="${3:-}"
  [ -n "$pr" ] || refuse "usage: backup.sh merge <pr> --confirm"
  [ "$merge_confirm" = "--confirm" ] || refuse \
    "merge requires separate per-PR --confirm approval."
  say "[$(ts)] Merging PR #$pr into main (squash; delete remote branch)…"
  gh pr merge "$pr" --squash --delete-branch || exit 5
  state="$(gh pr view "$pr" --json state -q .state 2>/dev/null)"
  [ "$state" = "MERGED" ] || refuse "PR #$pr state is $state, not MERGED."
  current_branch="$(git branch --show-current)"
  git checkout -q main && git pull -q origin main || exit 7
  case "$current_branch" in
    librarian-sync-*) git branch -qD "$current_branch" 2>/dev/null || true ;;
  esac
  [ "$(git rev-parse HEAD)" = "$(git rev-parse origin/main)" ] || refuse \
    "merged PR but local main does not match origin/main."
  say "[$(ts)] MERGED: PR #$pr; local main matches origin/main."
  exit 0
fi

confirm=0
backup_paths=()
while [ "$#" -gt 0 ]; do
  case "$1" in
    --confirm)
      confirm=1
      shift
      ;;
    --path)
      [ "$#" -ge 2 ] || refuse "--path requires a repository-relative file."
      candidate="$2"
      case "$candidate" in
        ""|/*|"."|".."|../*|*/../*|*/..|./*|*/./*|*/.)
          refuse "unsafe reviewed path: $candidate"
          ;;
      esac
      [ ! -d "$candidate" ] || refuse \
        "--path must name an exact file, not a directory: $candidate"
      if [ ! -e "$candidate" ] && ! git ls-files --error-unmatch -- "$candidate" \
        >/dev/null 2>&1; then
        refuse "reviewed path does not exist and is not a tracked deletion: $candidate"
      fi
      duplicate=0
      if [ "${#backup_paths[@]}" -gt 0 ]; then
        for reviewed in "${backup_paths[@]}"; do
          [ "$reviewed" = "$candidate" ] && duplicate=1
        done
      fi
      [ "$duplicate" -eq 1 ] || backup_paths+=("$candidate")
      shift 2
      ;;
    *)
      refuse "unknown argument: $1"
      ;;
  esac
done

[ "${#backup_paths[@]}" -gt 0 ] || refuse \
  "at least one explicit --path is required."
[ "$(git branch --show-current)" = "main" ] || refuse \
  "backup must start from main."
git diff --cached --quiet || refuse \
  "the Git index already contains staged changes."

integrity_gate
git add -A -- "${backup_paths[@]}"
guard_exact_staged_allowlist
guard_no_symlink_or_gitlink

if git diff --cached --quiet; then
  say "[$(ts)] Nothing to back up in the reviewed path allowlist."
  reset_reviewed_paths
  exit 0
fi

secret_scan
say "[$(ts)] Reviewed paths that would be backed up:"
git diff --cached --stat | sed 's/^/  /'

if [ "$confirm" -ne 1 ]; then
  say ""
  say "DRY RUN — no branch, commit, push, or PR."
  reset_reviewed_paths
  exit 0
fi

branch="librarian-sync-$(stamp)"
say "[$(ts)] Creating branch $branch from main…"
git checkout -q -b "$branch" || {
  reset_reviewed_paths
  exit 10
}
git commit -q -m "skills backup $(ts)" || exit 5
say "[$(ts)] Pushing reviewed branch…"
git push -q -u origin "$branch" || exit 6
say "[$(ts)] Opening review PR…"
pr_url="$(gh pr create --base main --head "$branch" \
  --title "Skills backup $(ts)" \
  --body "Path-limited Codex skills-librarian backup. Installed-shelf integrity clean; exact staged allowlist reviewed; staged diff secret-scanned. Review before merge." \
  2>&1)" || {
  say "PR creation failed: $pr_url"
  exit 11
}
say "[$(ts)] PR OPENED: $pr_url"
say "The PR is unmerged. Merge requires separate per-PR approval."
