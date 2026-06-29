---
name: cloud-run-reauth
description: Restore and use gcloud access to TigerClaw prod (Cloud Run + Cloud SQL + Secret Manager) when the daily-expiring tokens have lapsed. Run an auth pre-check up front so a task never half-stalls; on expiry, run the interactive reauth (one browser sign-in); start cloud-sql-proxy; and fetch Secret Manager secrets as RAW BYTES (encoding the trailing-newline gotcha so HMAC/encryption never silently mismatches). Use when a gcloud/Secret-Manager/Cloud SQL command returns expired/Unauthorized, before any prod-DB or Secret-Manager work, or when Brent says "reauth", "gcloud is expired", "run the cloud run reauth", "start the proxy", or asks to operate against prod. Companion to ship-it (which assumes GCP is already reachable).
---

# cloud-run-reauth

The gcloud auth + safe prod-access layer. TigerClaw's gcloud **user token and ADC both expire ~daily**, which silently blocks Secret Manager, Cloud SQL (via cloud-sql-proxy), and `gcloud run` calls mid-task. This skill makes that a 15-second, well-signposted step instead of a stall — and bakes in the two hard-won gotchas (the trailing-newline secret bug; reuse-the-shared-proxy) so neither of us re-derives them.

It does **not** create any long-lived credential. Reauth is the interactive Google sign-in (user-cred OAuth requires the click). A non-interactive service-account-key version was explicitly **declined** for security reasons — do not add one without Brent's explicit say-so.

Script: `scripts/cloud-run-reauth.sh` (defaults are correct for prod; override `PROJECT_ID` / `SQL_INSTANCE` / `PROXY_PORT` via env).

## Hard rules

- **Pre-check BEFORE prod work, not after a failure.** Run `check` (or `ensure`) at the start of any task that touches Secret Manager, the prod DB, or `gcloud run`. Discovering expiry half-way through is the failure mode this skill exists to kill.
- **Reauth is interactive — Brent completes the browser sign-in.** The skill can launch `gcloud auth login` / `application-default login` (they open a browser on his Mac and finish automatically), but he must complete each. Both must land — they are independent (user token vs ADC).
- **Secrets: raw bytes only, never printed.** TigerClaw's GCP secrets carry a **trailing `\n`** that Cloud Run injects into env verbatim. `VALUE=$(gcloud secrets access …)` strips it → any HMAC (session tokens) or key derivation (encryptToken/getEncKey) **mismatches** → 401 / decrypt-fail. Always fetch with `secret <name> <outfile>` (raw file) and read the exact bytes. Confirmed for `tiger-claw-wizard-session-secret` (65B, ends `0a`) and `tiger-claw-encryption-key`. The prod service is internally consistent (signs+verifies with the same newline'd value) — this only bites local tooling. **Never echo a secret value**; the script prints byte counts only. **Shred** secret files when done (`rm -f`).
- **Reuse the shared proxy.** One cloud-sql-proxy on the default port (5433); `proxy` is idempotent. Don't spawn duplicates.
- **Prod-DB writes are surgery.** If a task seeds prod (e.g. a throwaway tenant to exercise a deployed endpoint), it MUST clean up after itself and VERIFY the cleanup (0 leftovers), and use an obvious throwaway slug. Stop the proxy at the end.

## Workflow

1. **Unblock auth (one call):**
   `bash scripts/cloud-run-reauth.sh ensure`
   — checks both tokens; if either is expired, launches the interactive reauth; re-checks. (Use `check` for a pure read-only status, `login` to force the browser flow.) Tell Brent to complete the browser sign-in(s) when they pop.
2. **Start the proxy** (only if you need the prod DB):
   `bash scripts/cloud-run-reauth.sh proxy`   → listens on 127.0.0.1:5433.
3. **Fetch secrets as raw bytes** (only what you need):
   `bash scripts/cloud-run-reauth.sh secret tiger-claw-database-url /tmp/dburl.bin`
   Then in code read the exact bytes. For the DB URL, strip trailing whitespace and rewrite host→`127.0.0.1:<port>` for the proxy. For HMAC/encryption secrets, use the bytes **as-is** (with the newline).
4. **Do the prod work** (hit live endpoints, query the DB, etc.). For driving session-gated routes, mint the session exactly as the platform does — `base64url(JSON({data,sig}))` where `data=JSON.stringify({email,userId,flavor:"recruiting",botId,issuedAt,expiresAt})` (Unix seconds) and `sig=HMAC-SHA256(<raw WIZARD_SESSION_SECRET bytes>, data).hex`; `resolveTenant` requires `session.botId === tenant.id`.
5. **Clean up:** shred secret files (`rm -f /tmp/*.bin`), and `bash scripts/cloud-run-reauth.sh stop-proxy` when finished. If you seeded the prod DB, delete the scaffolding and verify 0 leftovers first.

## Notes

- `gcloud` expiry is the cause of: Secret Manager `access` returning empty, cloud-sql-proxy "server closed the connection unexpectedly", and `gcloud run describe` failures. When any of those appear, suspect auth first → `ensure`.
- Reauth lapses roughly daily; expect to run `ensure` near the start of most prod-touching sessions.
- Companion skills: **ship-it** (merge → deploy → live `/health` verify) assumes GCP is already reachable — run `ensure` first if its deploy/health steps can't read prod. **doc-keeper** logs results to VERIFIED.md/SOTU.
