#!/usr/bin/env bash
# Allsup Leads — Veterans: one-command batch.
# Mines veterans-benefits-gap (Reddit + X + TikTok, keyless, fresh) -> tiers by need
# (owed-but-not-getting / in-motion / eligibility) -> writes VETERANS-LEADS-<date>.csv/.md
# to the Desktop -> builds the browsable book (index.html) into a publish dir.
# Does NOT run any heavy resolver. Does NOT send email (agent step).
#
# Usage: run.sh [--days N]   (default 30)
set -euo pipefail

DAYS=30
[ "${1:-}" = "--days" ] && DAYS="${2:?--days needs a value}"

SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PULL="$SKILL_DIR/scripts/veterans_pull.py"
DATAMINE_BIN_DEFAULT="$HOME/Datamine/.venv/bin/datamine"
DATE="$(date +%F)"
DESKTOP="$HOME/Desktop"
BOOK_DIR="$SKILL_DIR/.book"

export DATAMINE_BIN="${DATAMINE_BIN:-$DATAMINE_BIN_DEFAULT}"
[ -x "$DATAMINE_BIN" ] || { echo "ERROR: datamine bin not executable: $DATAMINE_BIN"; exit 1; }

# Oxylabs = OPTIONAL (speed only; Reddit is keyless). No-op if not gcloud-authed.
export OXYLABS_USERNAME="${OXYLABS_USERNAME:-$(gcloud secrets versions access latest --secret=oxylabs-username 2>/dev/null || true)}"
export OXYLABS_PASSWORD="${OXYLABS_PASSWORD:-$(gcloud secrets versions access latest --secret=oxylabs-password 2>/dev/null || true)}"
[ -n "$OXYLABS_USERNAME" ] && echo "Oxylabs proxy: loaded (faster Reddit)" || echo "Oxylabs proxy: not loaded — direct fetch (still works, slower)"

echo "== pulling veterans-benefits-gap (Reddit + X + TikTok, ${DAYS}d, fresh, tiered) =="
python3 "$PULL" --full --days "$DAYS" --outdir "$DESKTOP"

CSV="$DESKTOP/VETERANS-LEADS-$DATE.csv"
[ -f "$CSV" ] || { echo "ERROR: expected CSV not found: $CSV"; exit 1; }

echo "== building the book =="
rm -rf "$BOOK_DIR"; mkdir -p "$BOOK_DIR"
python3 "$SKILL_DIR/scripts/build_book.py" "$CSV" "$BOOK_DIR"

echo
echo "DONE."
echo "  CSV  : $CSV"
echo "  MD   : $DESKTOP/VETERANS-LEADS-$DATE.md"
echo "  BOOK : $BOOK_DIR/index.html   (publish next — see SKILL.md)"
