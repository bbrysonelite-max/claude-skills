# Refine — reference

## Gotchas log (earned the hard way — don't re-learn these)

1. **Oxylabs creds.** Both Datamine's Reddit surface and blue-healer use the Web Scraper API,
   which authenticates with `OXYLABS_USERNAME` + `OXYLABS_PASSWORD` — the **API sub-user** from
   the dashboard's Web Scraper API product, found under its Authentication section.
   - NOT your account login email (an `@` in the username → HTTP 401).
   - NOT `OXYLABS_API_KEY` (a different credential neither tool reads).
   - Always `python3 scripts/refine.py envcheck` before a run; expect `HTTP 200 -> OK`.

2. **`kloop.env` is not shell-sourceable.** It contains prose/notes between assignments, so
   `set -a; . kloop.env` errors out partway and silently fails to load later vars. Parse only
   lines matching `^KEY=VALUE` (the helper's `load_env()` does this).

3. **Don't disable TLS verification.** Creds ride in auth headers; use a verified context
   (`certifi` if available). If you hit `CERTIFICATE_VERIFY_FAILED`, fix the trust store /
   install `certifi` — do not set `CERT_NONE`.

4. **maigret data path (fixed upstream).** blue-healer once hardcoded its maigret `data.json`
   to a Replit `.pythonlibs/` path; outside Replit every search errored with "Problem while
   attempting to access data file" and returned 0 records. Fixed in PR #1 (resolve via
   `maigret.__file__`). A fresh clone works; if you see that error, you're on an old checkout.

5. **Sherlock vs identity.** Sherlock matches a username *string* across sites — multi-platform
   presence for a distinctive handle is very likely one person; for short/generic handles it can
   be different people. Use `--min-platforms` (default 2) to cut collision noise. blue-healer's
   `recursive+enrich` pulls names/bios that help disambiguate.

6. **Handles with dots/specials** (`name.surname`, `foo.com`) fail on most Sherlock sites — the
   `usernames` step drops them. Quora ore rows have no handle and are skipped entirely.

7. **blue-healer is a web app.** Runs `app.run(port=5000)` by default; `app/` must be on
   `sys.path` (run from inside `app/`). The helper picks a free port and launches its own copy.

## blue-healer /api contract

- `GET  /api/enrichment-status` → `{available, providers[], keyed[], builtin[]}` (use to confirm keys loaded)
- `POST /api/search` body: `{usernames: "a, b, c", timeout, recursive, max_depth (≤2), enrich, domains, proxies}` → `{job_id}`
- `GET  /api/job/<id>` → `{status: queued|running|done|error, record_count, card_count, error_count, errors[], records[], cards[]}`
- `GET  /api/job/<id>/download/<json|csv>` → full export (`{contact_cards[], profiles[]}` for json); only when `status==done`
- `POST /api/job/<id>/rerun` → new `{job_id}` with same params

A contact card aggregates one root's recursive runs: name, location, bio, avatar, IDs, profile
URLs, and candidate emails (each with `deliverable|undeliverable|catch_all|unknown`).

## Deliverable (settled)

**Individuals are the only valuable deliverable** (Brent, standing rule 2026-06-29): reachable
individual claimants carrying the signal. Orgs / lawyers / provider directories = ZERO value —
`classify` drops them to `orgs_dropped.txt` and they are never offered. The SSDI→Allsup model
targets individual claimants ($500/lead). Brent (compliance authority) has already decided to
resolve individuals — **do NOT re-ask the org-vs-individual question each run.** Keep the
public-data discipline (handles that already posted publicly), and run the resolve.

## Output layout (convention, mirrors `/mine`'s `/tmp/mine-<vertical>`)

```
/tmp/refine-<vertical>/
  usernames.txt          # clean, deduped
  sherlock/<user>.csv    # one per username (osint output)
  confirmed.txt          # >= min-platforms
  individuals.txt        # THE deliverable (resolve this)
  orgs_dropped.txt       # discard log — zero value, never resolved
  contact_cards.json     # blue-healer export for the resolved group
```
