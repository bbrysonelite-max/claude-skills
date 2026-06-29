#!/usr/bin/env bash
# skills-librarian backup — keep the GitHub mirror of ~/.claude/skills current.
# The librarian owns this: after audit + index reconcile, sync the shelf to its private remote.
# Rules baked in (Brent's): integrity must be clean first; SECRET-SCAN the staged diff before
# any commit; never back up symlinks-as-pointers or nested repos; the ONLY mutation (commit+push)
# refuses to run without --confirm. main IS the backup on this mirror repo (not a PR/deploy repo).
set -uo pipefail

SKILLS_DIR="${SKILLS_DIR:-$HOME/.claude/skills}"
LIBRARIAN_DIR="$SKILLS_DIR/skills-librarian"
ts(){ date -u +"%Y-%m-%dT%H:%M:%SZ"; }
say(){ printf '%s\n' "$*"; }

cd "$SKILLS_DIR" 2>/dev/null || { say "ERROR: skills dir not found at $SKILLS_DIR"; exit 1; }
git rev-parse --is-inside-work-tree >/dev/null 2>&1 || { say "ERROR: $SKILLS_DIR is not a git repo"; exit 1; }
git remote get-url origin >/dev/null 2>&1 || { say "ERROR: no 'origin' remote (run the one-time backup init first)"; exit 1; }

confirm="${1:-}"

# 1) Integrity gate — never back up a broken shelf.
say "[$(ts)] Integrity gate (audit.py)…"
if ! python3 "$LIBRARIAN_DIR/scripts/audit.py" >/dev/null 2>&1; then
  say "REFUSING to back up: integrity issues present. Run: python3 audit.py  — fix, then retry."
  exit 2
fi
say "  integrity clean."

# 2) Stage everything (symlinks + nested repos are .gitignored, so this is safe).
git add -A

# 3) Guard: refuse to commit a symlink or a gitlink (nested repo) that slipped past .gitignore.
bad="$(git diff --cached --name-only | while read -r f; do
  [ -L "$f" ] && { echo "SYMLINK:$f"; continue; }
  mode="$(git ls-files --stage -- "$f" 2>/dev/null | awk '{print $1}')"
  [ "$mode" = "160000" ] && echo "GITLINK:$f"
done)"
if [ -n "$bad" ]; then
  say "REFUSING: a symlink or nested repo is staged (add it to .gitignore first):"
  printf '  %s\n' $bad
  git reset -q
  exit 3
fi

# 4) Anything to do?
if git diff --cached --quiet; then
  head="$(git rev-parse HEAD)"; remote="$(git rev-parse '@{u}' 2>/dev/null || echo none)"
  if [ "$head" = "$remote" ]; then say "[$(ts)] Already in sync (HEAD==origin: ${head:0:7}). Nothing to back up."; exit 0; fi
  say "[$(ts)] No local changes, but HEAD ($(echo "$head"|cut -c1-7)) != origin ($(echo "$remote"|cut -c1-7)) — a push is pending."
fi

# 5) SECRET SCAN the staged diff (hard stop). Reference keys by name only — never echo a value.
# Patterns require an actual payload (a key prefix + length, a PEM header, or NAME=value) so the
# scan flags real leaks, not the bare words appearing in code/docs (or in this scanner itself).
say "[$(ts)] Secret-scanning staged diff…"
SECRET_RE='(sk_|sk-|blt_|AIza|AKIA|ghp_|xox)[A-Za-z0-9_/+-]{12,}|-----BEGIN[A-Z ]+PRIVATE KEY|(api[_-]?key|client_secret|[A-Za-z0-9]*_SECRET|[A-Za-z0-9]*_TOKEN|password)[[:space:]"]*[:=][[:space:]"]*[^[:space:]"]{6,}'
hits="$(git diff --cached -U0 | grep -nE '^\+' | grep -vE '^[0-9]+:\+\+\+' | grep -iE "$SECRET_RE" 2>/dev/null || true)"
if [ -n "$hits" ]; then
  say "STOP: possible secret(s) in the staged diff. NOT committing. Locations only (values withheld):"
  printf '%s\n' "$hits" | sed -E 's/([:=]).*/\1 <redacted>/' | cut -c1-80 | head -40
  git reset -q
  exit 4
fi
say "  secret scan clean."

# 6) Show the plan.
say "[$(ts)] Staged changes:"
git diff --cached --stat | sed 's/^/  /'

if [ "$confirm" != "--confirm" ]; then
  say ""
  say "DRY RUN — nothing committed or pushed. To back up for real:"
  say "  skills-librarian/scripts/backup.sh --confirm"
  git reset -q
  exit 0
fi

# 7) Commit + push (the only mutation).
msg="skills backup $(ts)"
say "[$(ts)] Committing: $msg"
git commit -q -m "$msg" || { say "commit failed"; exit 5; }
say "[$(ts)] Pushing to origin/main…"
git push -q origin HEAD:main || { say "PUSH FAILED — backup is NOT current. Check network/auth."; exit 6; }

# 8) Verify HEAD == origin (ground-truth, don't claim).
git fetch -q origin main 2>/dev/null || true
head="$(git rev-parse HEAD)"; remote="$(git rev-parse origin/main 2>/dev/null)"
if [ "$head" = "$remote" ]; then
  say "[$(ts)] BACKED UP ✅  HEAD==origin/main (${head:0:7})  remote=$(git remote get-url origin)"
else
  say "[$(ts)] PUSHED but HEAD ($(echo "$head"|cut -c1-7)) != origin ($(echo "$remote"|cut -c1-7)) — VERIFY MANUALLY."
  exit 7
fi
