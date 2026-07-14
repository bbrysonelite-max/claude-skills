#!/usr/bin/env bash
# cloud-run-reauth.sh — safe, repeatable gcloud auth + prod-access primitives for TigerClaw.
#
# Subcommands:
#   check                       Read-only. Report whether the gcloud USER token and ADC token are
#                               live. Exit 0 only if BOTH are valid; exit 3 if either is expired.
#   login                       Interactive. Run `gcloud auth login` + `application-default login`
#                               (each opens a browser; Brent completes the sign-in). Re-checks after.
#   ensure                      check; if expired, run login; then check again. The one-call unblocker.
#   proxy [port]                Start cloud-sql-proxy to the prod instance (default port 5433).
#                               Idempotent: no-op if something is already listening on the port.
#   stop-proxy [port]           Kill the cloud-sql-proxy started on that port (default 5433).
#   secret <name> <outfile>     Fetch a Secret Manager secret to <outfile> as RAW BYTES (preserving
#                               any trailing newline). umask 077. Prints byte count only — NEVER the value.
#   status                      One-shot: auth + project + proxy state.
#
# Defaults are correct for TigerClaw prod; override via env:
PROJECT_ID="${PROJECT_ID:-hybrid-matrix-472500-k5}"
SQL_INSTANCE="${SQL_INSTANCE:-hybrid-matrix-472500-k5:us-central1:tiger-claw-postgres-ha}"
PROXY_PORT_DEFAULT="${PROXY_PORT:-5433}"

set -uo pipefail

user_ok () { gcloud auth print-access-token >/dev/null 2>&1; }
adc_ok  () { gcloud auth application-default print-access-token >/dev/null 2>&1; }

cmd_check () {
  local u a
  if user_ok; then u="OK"; else u="EXPIRED"; fi
  if adc_ok;  then a="OK"; else a="EXPIRED"; fi
  echo "account: $(gcloud config get-value account 2>/dev/null)"
  echo "user token: $u"
  echo "ADC token:  $a"
  [ "$u" = "OK" ] && [ "$a" = "OK" ] && return 0 || return 3
}

cmd_login () {
  # Interactive — each opens a browser on this Mac; complete the Google sign-in there.
  if user_ok; then echo "user token already valid — skipping gcloud auth login"; else
    echo ">>> gcloud auth login (complete the browser sign-in)…"; gcloud auth login || return 1; fi
  if adc_ok; then echo "ADC token already valid — skipping application-default login"; else
    echo ">>> gcloud auth application-default login (complete the browser sign-in)…"; gcloud auth application-default login || return 1; fi
  echo "--- re-check ---"; cmd_check
}

cmd_ensure () {
  if cmd_check >/dev/null 2>&1; then echo "auth already live:"; cmd_check; return 0; fi
  echo "auth expired — launching interactive reauth…"; cmd_login
}

proxy_pid_on () { lsof -nP -iTCP:"$1" -sTCP:LISTEN -t 2>/dev/null | head -1; }

cmd_proxy () {
  local port="${1:-$PROXY_PORT_DEFAULT}"
  if [ -n "$(proxy_pid_on "$port")" ]; then echo "proxy already listening on $port (pid $(proxy_pid_on "$port"))"; return 0; fi
  if ! command -v cloud-sql-proxy >/dev/null 2>&1; then echo "ERROR: cloud-sql-proxy not on PATH" >&2; return 1; fi
  if ! adc_ok; then echo "ERROR: ADC token expired — run '$0 login' first (proxy needs ADC)" >&2; return 3; fi
  local log; log="$(mktemp)"
  cloud-sql-proxy --port "$port" "$SQL_INSTANCE" >"$log" 2>&1 &
  local i; for i in $(seq 1 15); do [ -n "$(proxy_pid_on "$port")" ] && break; sleep 1; done
  if [ -n "$(proxy_pid_on "$port")" ]; then echo "proxy up on 127.0.0.1:$port (pid $(proxy_pid_on "$port"))"; else
    echo "ERROR: proxy failed to start:" >&2; tail -3 "$log" >&2; return 1; fi
}

cmd_stop_proxy () {
  local port="${1:-$PROXY_PORT_DEFAULT}"
  pkill -f "cloud-sql-proxy --port $port" 2>/dev/null && echo "proxy on $port stopped" || echo "no proxy on $port"
}

cmd_secret () {
  # RAW-BYTE fetch. GCP secrets here carry a trailing \n that Cloud Run injects verbatim;
  # any HMAC/encryption MUST use these exact bytes. gcloud does not append a newline, so the
  # file holds the secret's own bytes. NEVER print the value.
  local name="${1:-}" out="${2:-}"
  if [ -z "$name" ] || [ -z "$out" ]; then echo "usage: $0 secret <secret-name> <outfile>" >&2; return 2; fi
  if ! user_ok; then echo "ERROR: user token expired — run '$0 login' first" >&2; return 3; fi
  umask 077
  if gcloud secrets versions access latest --secret="$name" --project="$PROJECT_ID" > "$out" 2>/dev/null; then
    echo "wrote $out ($(wc -c < "$out" | tr -d ' ') bytes, raw — value NOT printed). Remember to shred it when done."
  else
    echo "ERROR: failed to fetch secret '$name' (expired auth? wrong name?)" >&2; rm -f "$out"; return 1
  fi
}

cmd_status () {
  cmd_check; local rc=$?
  echo "project: $PROJECT_ID"
  echo "sql instance: $SQL_INSTANCE"
  local p; p="$(proxy_pid_on "$PROXY_PORT_DEFAULT")"
  if [ -n "$p" ]; then echo "proxy on $PROXY_PORT_DEFAULT: up (pid $p)"; else echo "proxy on $PROXY_PORT_DEFAULT: down"; fi
  return $rc
}

case "${1:-}" in
  check)       shift; cmd_check "$@";;
  login)       shift; cmd_login "$@";;
  ensure)      shift; cmd_ensure "$@";;
  proxy)       shift; cmd_proxy "$@";;
  stop-proxy)  shift; cmd_stop_proxy "$@";;
  secret)      shift; cmd_secret "$@";;
  status)      shift; cmd_status "$@";;
  *) echo "usage: $0 {check|login|ensure|proxy [port]|stop-proxy [port]|secret <name> <outfile>|status}" >&2; exit 2;;
esac
