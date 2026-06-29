#!/usr/bin/env bash
# context-keeper — scaffold the next append-only session flight-recorder file.
# Deterministic: computes the next session number from what's on disk (handles gaps),
# stamps today's date, and writes a skeleton for the agent to fill. Never overwrites.
set -uo pipefail

DIR="${CONTEXT_KEEPER_DIR:-$HOME/tiger-claw-v4-core/.claude/sessions}"
mkdir -p "$DIR"

last="$(ls -1 "$DIR" 2>/dev/null | grep -oE 'session-[0-9]+' | grep -oE '[0-9]+' | sort -n | tail -1)"
next=$(( ${last:-0} + 1 ))
date="$(date +%Y-%m-%d)"
file="$DIR/${date}_session-${next}.md"

case "${1:-}" in
  --number) echo "$next"; exit 0;;          # read-only: next session number
  --path)   echo "$file"; exit 0;;          # read-only: target path
  --dir)    echo "$DIR"; exit 0;;
esac

headline="${1:-<one to three lines: the arc of this session>}"
if [ -e "$file" ]; then
  echo "EXISTS: $file (refusing to overwrite — flight recorder is append-only)"; exit 2
fi

cat > "$file" <<EOF
# Session ${next} — ${date}

${headline}

---

## 1. Decisions
- <what was decided, and what was RULED OUT (keep the ruled-out — it stops re-litigation)>

## 2. Discoveries
- <what we learned about the system / ground truth that wasn't obvious before>

## 3. Shipped / changed
- <PRs (numbers), merge SHAs, deploys — with UTC timestamps and live /health proof where it applies>

## 4. Verified vs unverified
- Verified live: <what was actually proven, how>
- NOT yet verified: <what is claimed but not exercised — name the gap, do not paper over it>

## 5. Open threads / next step
- <the single most concrete next action — this should feed NEXT_SESSION/handoff via doc-keeper>
EOF

echo "CREATED: $file"
