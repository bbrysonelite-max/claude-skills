#!/usr/bin/env bash
# skills-librarian backup — keep the GitHub mirror of ~/.claude/skills current via branch → PR → merge.
# Brent's rule (load-bearing): an AGENT NEVER TOUCHES main. Build on an isolated branch, open a PR,
# and merge into main only with his explicit per-PR approval. main is never pushed directly.
#
#   backup.sh                  dry-run: integrity-gate + secret-scan + show what WOULD sync (no mutation)
#   backup.sh --confirm        branch off main, commit, push branch, OPEN a PR. Does NOT merge.
#   backup.sh merge <pr> --confirm   merge that PR into main (his approval), sync local main, clean up
#
# Mechanical note: this live dir IS the work tree Claude loads skills from, so after --confirm the
# working tree stays ON the sync branch (the new/edited skills live there until merge). `merge`
# returns it to main. Integrity must be clean and the staged diff secret-scanned before any commit.
set -uo pipefail

SKILLS_DIR="${SKILLS_DIR:-$HOME/.claude/skills}"
LIBRARIAN_DIR="$SKILLS_DIR/skills-librarian"
ts(){ date -u +"%Y-%m-%dT%H:%M:%SZ"; }
stamp(){ date -u +"%Y%m%d-%H%M%S"; }
say(){ printf '%s\n' "$*"; }

cd "$SKILLS_DIR" 2>/dev/null || { say "ERROR: skills dir not found at $SKILLS_DIR"; exit 1; }
git rev-parse --is-inside-work-tree >/dev/null 2>&1 || { say "ERROR: $SKILLS_DIR is not a git repo"; exit 1; }
git remote get-url origin >/dev/null 2>&1 || { say "ERROR: no 'origin' remote (run the one-time backup init first)"; exit 1; }

# ---- shared gates -----------------------------------------------------------
integrity_gate(){
  say "[$(ts)] Integrity gate (audit.py)…"
  if ! python3 "$LIBRARIAN_DIR/scripts/audit.py" >/dev/null 2>&1; then
    say "REFUSING: integrity issues present. Run: python3 audit.py — fix, then retry."; exit 2
  fi
  say "  integrity clean."
}

guard_no_symlink_or_gitlink(){
  local bad
  bad="$(git diff --cached --name-only | while read -r f; do
    [ -L "$f" ] && { echo "SYMLINK:$f"; continue; }
    [ "$(git ls-files --stage -- "$f" 2>/dev/null | awk '{print $1}')" = "160000" ] && echo "GITLINK:$f"
  done)"
  if [ -n "$bad" ]; then
    say "REFUSING: a symlink or nested repo is staged (add it to .gitignore first):"
    printf '  %s\n' $bad; git reset -q; exit 3
  fi
}

secret_scan(){ # hard stop. references locations only — never a value. Two passes:
  say "[$(ts)] Secret-scanning staged diff…"
  local PREFIX_RE GENERIC_RE added added_owncode hits
  # Pass 1 — high-signal KEY LITERALS (real API keys / PEM). Zero false positives on prose/code;
  # applied to EVERYTHING, including the third-party .agents-backup/ mirror.
  # leading [^A-Za-z0-9] boundary so "sk-" inside words (ta-sk-, fla-sk-cors) doesn't match; 16+ payload.
  PREFIX_RE='(^|[^A-Za-z0-9])(sk-|sk_|blt_|AIza|AKIA|ghp_|xox)[A-Za-z0-9_/+-]{16,}|-----BEGIN[A-Z ]+PRIVATE KEY'
  # Pass 2 — generic NAME=value heuristic (credential-shaped value: quoted or digit-bearing). Noisy on
  # files full of *_secret/*_token IDENTIFIERS, so it SKIPS .agents-backup/ — that's third-party prompt
  # text (the GSD pack) already ground-truthed to contain no key literals; Pass 1 still covers it.
  GENERIC_RE='(api[_-]?key|client_secret|[A-Za-z0-9]*_secret|[A-Za-z0-9]*_token|password)[[:space:]"]*[:=][[:space:]"]*("[^"]{6,}|[A-Za-z0-9_/.+-]*[0-9][A-Za-z0-9_/.+-]*)'
  added="$(git diff --cached -U0 | grep -nE '^\+' | grep -vE '^[0-9]+:\+\+\+' || true)"
  added_owncode="$(git diff --cached -U0 -- . ':(exclude).agents-backup/**' | grep -nE '^\+' | grep -vE '^[0-9]+:\+\+\+' || true)"
  hits="$(printf '%s\n' "$added" | grep -iE "$PREFIX_RE" 2>/dev/null || true)"
  hits="$hits
$(printf '%s\n' "$added_owncode" | grep -iE "$GENERIC_RE" 2>/dev/null || true)"
  hits="$(printf '%s\n' "$hits" | grep -vE '^[[:space:]]*$' || true)"
  if [ -n "$hits" ]; then
    say "STOP: possible secret(s) in the staged diff. NOT committing. Locations only (values withheld):"
    printf '%s\n' "$hits" | sed -E 's/([:=]).*/\1 <redacted>/' | cut -c1-80 | head -40
    git reset -q; exit 4
  fi
  say "  secret scan clean."
}

# ---- merge mode -------------------------------------------------------------
if [ "${1:-}" = "merge" ]; then
  pr="${2:-}"; confirm="${3:-}"
  [ -n "$pr" ] || { say "usage: backup.sh merge <pr> --confirm"; exit 1; }
  if [ "$confirm" != "--confirm" ]; then
    say "REFUSING to merge PR #$pr without --confirm (per-PR approval is Brent's call)."; exit 2
  fi
  say "[$(ts)] Merging PR #$pr into main (squash, delete remote branch)…"
  gh pr merge "$pr" --squash --delete-branch || { say "merge failed"; exit 5; }
  state="$(gh pr view "$pr" --json state -q .state 2>/dev/null)"
  [ "$state" = "MERGED" ] || { say "STATE=$state — NOT MERGED. Stop."; exit 6; }
  cur="$(git branch --show-current)"
  git checkout -q main && git pull -q origin main || { say "local main sync failed — pull manually"; exit 7; }
  case "$cur" in librarian-sync-*) git branch -qD "$cur" 2>/dev/null || true;; esac
  head="$(git rev-parse HEAD)"; remote="$(git rev-parse origin/main 2>/dev/null)"
  if [ "$head" = "$remote" ]; then
    say "[$(ts)] MERGED ✅  PR #$pr → main; local main==origin/main (${head:0:7})"
  else
    say "[$(ts)] merged but local main ($(echo "$head"|cut -c1-7)) != origin ($(echo "$remote"|cut -c1-7)) — VERIFY."; exit 8
  fi
  exit 0
fi

# ---- dry-run / --confirm (branch + PR) --------------------------------------
confirm="${1:-}"
integrity_gate

# Must start from a clean main (never branch off a half-finished sync branch).
cur="$(git branch --show-current)"
if [ "$cur" != "main" ]; then
  say "REFUSING: on branch '$cur', not main. An earlier sync PR is likely still open —"
  say "merge it first ( backup.sh merge <pr> --confirm ), then re-run."; exit 9
fi

# Mirror ~/.claude/agents into the repo (dot-dir, so the skill loader + audit skip it) so
# AGENT definitions are backed up too — they live outside ~/.claude/skills and would otherwise
# never reach the mirror. A true mirror (deletes removed agents).
AGENTS_SRC="${AGENTS_SRC:-$HOME/.claude/agents}"
if [ -d "$AGENTS_SRC" ]; then
  if command -v rsync >/dev/null 2>&1; then
    rsync -a --delete --exclude '.DS_Store' --exclude '__pycache__' "$AGENTS_SRC/" "$SKILLS_DIR/.agents-backup/"
  else
    rm -rf "$SKILLS_DIR/.agents-backup"; mkdir -p "$SKILLS_DIR/.agents-backup"; cp -R "$AGENTS_SRC/." "$SKILLS_DIR/.agents-backup/"
  fi
  say "[$(ts)] Mirrored $(find "$AGENTS_SRC" -maxdepth 1 -name '*.md' | wc -l | tr -d ' ') agent file(s) → .agents-backup/"
fi

git add -A
guard_no_symlink_or_gitlink

if git diff --cached --quiet; then
  say "[$(ts)] Nothing to back up (no changes vs main). In sync."; git reset -q; exit 0
fi

secret_scan

say "[$(ts)] Changes that would be backed up:"
git diff --cached --stat | sed 's/^/  /'

if [ "$confirm" != "--confirm" ]; then
  say ""
  say "DRY RUN — no branch, no commit, no PR. To back up for real (opens a PR; you merge):"
  say "  skills-librarian/scripts/backup.sh --confirm"
  git reset -q
  exit 0
fi

# Real run: isolated branch → commit → push → PR. Never touches main.
branch="librarian-sync-$(stamp)"
say "[$(ts)] Creating branch $branch (off main)…"
git checkout -q -b "$branch" || { say "branch create failed"; exit 10; }
git commit -q -m "skills backup $(ts)" || { say "commit failed"; git checkout -q main; exit 5; }
say "[$(ts)] Pushing branch…"
git push -q -u origin "$branch" || { say "PUSH FAILED — backup not on remote. Check network/auth."; exit 6; }
say "[$(ts)] Opening PR…"
prurl="$(gh pr create --base main --head "$branch" \
  --title "Skills backup $(ts)" \
  --body "Automated skills-librarian backup. Integrity clean; staged diff secret-scanned. Review & merge to update the mirror." \
  2>&1)" || { say "PR create failed: $prurl"; exit 11; }
say "[$(ts)] PR OPENED ✅  $prurl"
say "  (working tree is now on $branch so live skills stay current.)"
say "  To consolidate after review:  backup.sh merge <pr#> --confirm"
