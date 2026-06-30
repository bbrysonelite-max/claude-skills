---
name: tiger-leader-hunt
description: Weekly discovery of NEW network-marketing leaders, coaches, trainers, and book authors with large teams (NuSkin + competitors) to partner with for a white-labeled Tiger. Use when the user says "leader hunt", "find leaders to partner with", "hunt for partners", or runs /tiger-leader-hunt.
user-invocable: true
allowed-tools: Bash, Read, Write
---

# tiger-leader-hunt

Discover NEW network-marketing **leaders, coaches, trainers, and book authors with large teams or audiences** — across NuSkin and competitors — that Brent can **partner with** (white-labeled Tiger). Target the **individual leader, never a company's front door**. This is a partner/BD hunt, not customer prospecting. Outreach is a separate later phase; this skill only FINDS and QUALIFIES.

## Hard rules
- Surface only people NOT seen before (use the ledger — Step 5).
- Bar = **Established + rising**: established leaders AND credible up-and-comers. DROP rank-and-file distributors with no audience/team signal, software competitors, and anything in `targeting.txt` `[exclude]`.
- Never invent handles or stats. Every candidate comes from real engine output.

## Step 1 — Read targeting
Read `targeting.txt` in this skill's directory. Parse the bracketed sections: `[platforms] [hashtags] [ranking_phrases] [hunt_brands] [authority_anchors] [subreddits] [exclude]`. Ignore `#` comment lines.

## Step 2 — Resolve the engine + Python
```bash
SKILL_DIR="$HOME/.claude/skills/tiger-leader-hunt"
ENGINE="$HOME/.claude/skills/last30days/scripts/last30days.py"
for py in python3.14 python3.13 python3.12 python3; do command -v "$py" >/dev/null 2>&1 && { "$py" -c 'import sys;exit(0 if sys.version_info>=(3,12) else 1)' && { PY="$py"; break; }; }; done
[ -f "$ENGINE" ] || { echo "ERROR: last30days engine not found at $ENGINE"; exit 1; }
```

## Step 3 — Build a leader-discovery query plan
Write a JSON plan to a tmpfile. Use the `[hashtags]` and `[ranking_phrases]` from targeting. Frame every `ranking_query` to find PEOPLE who are leaders, not products or pain. Example shape (substitute real targeting values):
```json
{
  "intent": "opinion",
  "freshness_mode": "balanced_recent",
  "cluster_mode": "none",
  "subqueries": [
    {"label": "leaders", "search_query": "network marketing leader coach trainer",
     "ranking_query": "Who is a network marketing or direct sales LEADER, coach, trainer, or book author with a large team or audience worth partnering with?",
     "sources": ["tiktok","instagram","youtube","x","reddit"], "weight": 1.0},
    {"label": "authors", "search_query": "network marketing author best selling book",
     "ranking_query": "Which network marketing authors or speakers are publishing books and training large audiences?",
     "sources": ["tiktok","instagram","youtube","x"], "weight": 0.9},
    {"label": "team_builders", "search_query": "built a team duplication downline leadership",
     "ranking_query": "Who is leading and teaching a large downline or team in direct selling?",
     "sources": ["tiktok","instagram","youtube","x"], "weight": 0.8}
  ]
}
```

## Step 4 — Run the engine
```bash
"$PY" "$ENGINE" "network marketing leaders to partner with" \
  --emit=compact --save-dir="$HOME/Documents/Last30Days" --save-suffix=leaderhunt \
  --plan "$PLAN_FILE" \
  --subreddits=<comma-joined [subreddits]> \
  --tiktok-hashtags=<comma-joined first ~6 [hashtags]> \
  --ig-creators=<optional known anchor handles>
```
Read the ENTIRE output. From the evidence clusters, collect the AUTHOR of each high-signal item as `platform:handle` (e.g. `instagram:toddfalcone`, `tiktok:fezknowzai`, `x:harkinsete`, `youtube:frazerbrookeschannel`).

## Step 5 — Dedup against the ledger
```bash
"$PY" "$SKILL_DIR/scripts/dedup.py" --seen "$SKILL_DIR/seen.txt" --check "<comma-joined platform:handle list>"
```
Only the ids it prints are NEW. Discard the rest. If nothing is new, tell the user the well is dry this week and suggest editing `targeting.txt`.

## Step 6 — Qualify, score, rank
For each NEW candidate, judge from their post text + visible profile:
- **Authority:** wrote a book; runs trainings/courses/challenges; "coach/mentor/trainer/speaker."
- **Scale:** follower/view counts; "my team / downline / students"; runs a community or challenge.
- **Company:** match against `[hunt_brands]` → tag NuSkin / competitor / unknown.
- **Stage:** Established (clear authority + size) or Rising (growing, building, teaching).
DROP rank-and-file with no audience, `[exclude]` entries, and software competitors (flag those as competitor intel, not targets). Rank by authority + scale + teaching signal, descending.

## Step 7 — Output
First line: `🐯 tiger-leader-hunt · <today's date> · <N new leaders>`
Then one card per candidate:
- **Name / @handle** as an inline markdown link.
- `Platform · Established|Rising · Company-tag`
- **Why qualified:** authority + scale evidence, quoted.
- **Recent hook:** their latest relevant post (the warm-open reason).
- **Reachability:** DM open? link in bio? book/site?
End with: the saved hunt-file path, and a one-line nudge that they can sharpen `targeting.txt` for next week.

## Step 8 — Record to the ledger
After presenting, append the surfaced handles so they never repeat:
```bash
"$PY" "$SKILL_DIR/scripts/dedup.py" --seen "$SKILL_DIR/seen.txt" --add "<comma-joined surfaced platform:handle list>"
```

## Improve loop
When the user says "add hashtag X", "drop Y", "this name was off", or "exclude Z": edit `targeting.txt` accordingly (add bad names to `[exclude]`). That is how the hunt sharpens over time.
