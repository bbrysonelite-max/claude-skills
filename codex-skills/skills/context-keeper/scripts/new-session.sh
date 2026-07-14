#!/usr/bin/env bash
# Scaffold the next append-only Codex context snapshot without overwriting.
set -uo pipefail

root="$(git rev-parse --show-toplevel 2>/dev/null || true)"
DIR="${CONTEXT_KEEPER_DIR:-${root:-$PWD}/.codex/sessions}"

last="$(ls -1 "$DIR" 2>/dev/null | grep -oE 'session-[0-9]+' | grep -oE '[0-9]+' | sort -n | tail -1)"
next=$(( ${last:-0} + 1 ))
date="$(date +%Y-%m-%d)"
file="$DIR/${date}_session-${next}.md"

case "${1:-}" in
  --number) echo "$next"; exit 0;;
  --path)   echo "$file"; exit 0;;
  --dir)    echo "$DIR"; exit 0;;
esac

headline="${1:-<one to three lines: the arc of this session>}"
mkdir -p "$DIR"

temp=""
cleanup() {
  if [[ -n "$temp" ]]; then
    rm -f -- "$temp"
  fi
}
trap cleanup EXIT HUP INT TERM

while :; do
  file="$DIR/${date}_session-${next}.md"
  temp="$(mktemp "$DIR/.new-session-XXXXXX")" || exit 1
  chmod 0644 "$temp" || exit 1
  if ! cat > "$temp" <<EOF
# Session ${next} - ${date}

${headline}

---

## 1. Decisions
- <what was decided, and what was RULED OUT (keep the ruled-out - it stops re-litigation)>

## 2. Discoveries
- <what we learned about the system / ground truth that wasn't obvious before>

## 3. Shipped / changed
- <PRs (numbers), merge SHAs, deploys - with UTC timestamps and live proof where it applies (a health check, a passing run, observed output)>

## 4. Verified vs unverified
- Verified live: <what was actually proven, how>
- NOT yet verified: <what is claimed but not exercised - name the gap, do not paper over it>

## 5. Open threads / next step
- <the single most concrete next action - this feeds the project's handoff/next-session doc>
EOF
  then
    exit 1
  fi

  if ln "$temp" "$file" 2>/dev/null; then
    rm -f -- "$temp"
    temp=""
    trap - EXIT HUP INT TERM
    echo "CREATED: $file"
    exit 0
  fi

  rm -f -- "$temp"
  temp=""
  if [[ -e "$file" || -L "$file" ]]; then
    next=$((next + 1))
    continue
  fi
  echo "ERROR: could not publish context snapshot: $file" >&2
  exit 1
done
