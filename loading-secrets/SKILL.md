---
name: loading-secrets
description: Use when any task needs an API key, token, login, or password — before searching for credentials, asking Brent for a key, or wiring a service. Also use when a key is missing, an env file can't be found, or you're about to cat/echo a credentials file.
---

# Loading Secrets

One canonical place per machine. Load by NAME. Never see, echo, or move the values.

## The Law (Brent's standing rules — do not renegotiate)

1. **Never accept a secret via chat.** If a key is missing, name the variable and ask Brent to add it to the sheet. File-on-target-machine handoff only.
2. **Never echo, print, log, or commit a secret value.** Report the variable NAME and the file PATH, never the value.
3. **Never write to the credentials sheet.** It is Brent-authored only. Agents read.
4. **Never copy secrets to another file or machine.** Load into process env at point of use.

## Canonical locations

| Machine | Path | Format | Verified |
|---|---|---|---|
| This iMac (2020iMac.local — the mirror) | `~/Desktop/GitSync/kloop.env` → symlink to `CREDENTIALSUPDATED08182026.md` | Markdown sheet containing `VAR=value` lines (34) | 2026-08-28 |
| This iMac (mirror sheet) | `~/Desktop/GitSync/Brents Credentials.md` (mode 400, synced from cheesegrater by credsync — mirror-verified every push) | Markdown, pointer of record | 2026-08-28 |
| Cheesegrater (2019cheesegrader.local, brentbryson@192.168.0.2) | MASTER: `~/.credsync/Brents Credentials.md` (mode 400). Also `~/.credsync/kloop.env` (mode 600, 31 vars, dated Aug 10 — likely STALE; the sheet is canon). SSH CANNOT read its `~/Desktop` (TCC) — use `~/.credsync`, never the Desktop path, over ssh. | Markdown sheet / dotenv | 2026-08-28 |
| VPS (pebo@2.24.70.63, srv1642065) | Per-service dotenv: `~/.hermes/.env` (22 vars), `~/.hermes/tigerclaw.env` (45 vars), `~/claw-catcher/.env` (7), `~/claw-catcher/stan-sync/.env` (7), `~/tiger-finder/.env` (1), `~/.config/watch/.env` (5), `~/actions-runner/.env` (1) | dotenv (real `source`-able files, unlike the Mac sheet) | 2026-08-28 |
| Tiger prod | GCP Secret Manager (project hybrid-matrix-472500-k5) — use `/cloud-run-reauth` | raw bytes; beware trailing newline | see that skill |

On the VPS, load from the `.env` of the service that owns the key — Hermes keys from `~/.hermes/`, Claw Catcher keys from `~/claw-catcher/.env`. Do not copy vars between service files.

**The sheet is NOT a clean dotenv file.** It is markdown with env-style lines inside. Never `source` it. Extract single lines only.

## Load by name (the only approved read)

```bash
# Load one secret into the current process env. Value never touches stdout.
get_secret() {
  local name="$1"
  local line
  line=$(grep -m1 "^${name}=" ~/Desktop/GitSync/kloop.env) || { echo "MISSING: $name (ask Brent to add it to the sheet)"; return 1; }
  export "$line"
  echo "loaded: $name"
}
get_secret BLOTATO_API_KEY   # → "loaded: BLOTATO_API_KEY"
```

**Load and use in the SAME shell invocation.** Env does not persist between tool calls — define `get_secret`, load, and run the command that needs `$VAR` in one Bash call.

To see what exists without seeing values:

```bash
grep -o '^[A-Za-z_][A-Za-z0-9_]*=' ~/Desktop/GitSync/kloop.env | sed 's/=$//'
```

## When a key is missing

Say exactly: "The sheet has no `VAR_NAME`. Add it to `~/Desktop/GitSync/kloop.env` (the sheet) and tell me." Then stop that thread. Do not accept the value in chat, do not hunt other files, do not guess.

## Red flags — STOP

- About to `cat`/`head`/Read the credentials sheet → you will see values. Grep the one line into `export` instead.
- About to paste a key into a command, file, or message → load into env and reference `$VAR`.
- Using a path from memory that you haven't listed this session → `ls` it first; this table's paths were wrong in memory once already ("GitSync Copy" never existed).
- "It's faster if Brent just pastes the key" → forbidden; the sheet is the handoff.

## Common mistakes

| Mistake | Fix |
|---|---|
| `source kloop.env` | It's markdown; parses garbage. `get_secret NAME` only. |
| mdfind/find hunting for creds | The table above is canonical. Hunt = wrong. |
| Reporting the value as proof it loaded | Proof is `loaded: NAME` + exit 0. |
| Editing the sheet to "help" | Brent-authored only. Report, don't write. |
