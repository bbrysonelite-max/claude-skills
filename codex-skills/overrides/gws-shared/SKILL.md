---
name: "gws-shared"
description: "gws CLI: Shared patterns for authentication, global flags, and output formatting."
---

# gws-shared

Apply the common access, routing, formatting, and safety rules for Google Workspace operations.

## Codex Runtime

- **Dependencies:** connected Google Workspace apps or gws CLI; Google Workspace credentials
- `connected Google Workspace apps or gws CLI`
- `Google Workspace credentials`
- **Execution:** Operate directly in the main Codex agent.
- Prefer connected Gmail/Google Drive app tools, Calendar, Tasks, or Chat capabilities when the required service is present; the `gws` CLI fallback covers unavailable connectors.
- Never print, log, or expose secret values.

## Inputs and Preflight

1. Identify the service, account context, resource identifiers, requested fields, and whether the action is Read-only or mutating.
2. Check for the matching connected capability first. If unavailable, confirm `gws` is on `PATH` and authenticated without displaying tokens or credential files.
3. For CLI fallback, inspect `gws schema <service>.<resource>.<method>` before constructing parameters.
4. Before any mutation, show the exact target and content or change, and obtain clear confirmation. Read-only calls may proceed without confirmation.

## Procedure

1. Use the narrowest connected-app read method available and request only needed fields.
2. If no connector covers the operation, use the fallback form:
   ```bash
   gws <service> <resource> <method> --params '<json>' --format json
   ```
3. Paginate deliberately with `--page-all` and a bounded `--page-limit` only when complete coverage is needed.
4. For a mutation, prefer a connector when present. Otherwise validate with `--dry-run` when supported, repeat the confirmed target and content, then execute once.
5. Use `--sanitize` when Workspace content contains sensitive personal information and sanitization is available.
6. Report resource IDs, URLs, counts, and status while withholding auth material and unnecessary message or document content.

## Safety and Errors

- Never expose API keys, OAuth tokens, service-account JSON, cookies, credential paths, or raw authorization headers.
- Never send, create, update, delete, announce, or upload without clear target/content confirmation.
- Quote JSON as one shell argument. Escape sheet-range exclamation marks safely for the active shell.
- On auth, permission, quota, schema, or partial-pagination failure, stop and report the operation and remediation without retrying mutations blindly.

## Output Contract

Return the route used (connector or `gws` fallback), service and account context without secrets, read scope or confirmed mutation target/content, result identifiers, pagination limits, and any partial or blocked state.
