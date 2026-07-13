---
name: "gws-workflow-weekly-digest"
description: "Google Workflow: Weekly summary: this week's meetings + unread email count."
---

# gws-workflow-weekly-digest

Summarize the week's meetings and unread-email count from a clearly bounded account and timezone.

## Codex Runtime

- **Dependencies:** connected Gmail, Calendar, and Drive apps or gws CLI; Google Workspace credentials
- `connected Gmail, Calendar, and Drive apps or gws CLI`
- `Google Workspace credentials`
- **Execution:** Operate directly in the main Codex agent.
- Prefer connected Gmail and Calendar capabilities, using connected Drive only for explicitly linked documents; the `gws` CLI fallback is `gws workflow +weekly-digest`.
- Never print, log, or expose secret values.

## Inputs and Preflight

1. Identify the account, calendar, timezone, week boundary, and whether linked Drive context is requested.
2. Check connected Gmail, Calendar, and Drive capabilities first. If required reads are unavailable, confirm `gws` authentication and inspect workflow help/schema.
3. This workflow is Read-only. It may proceed without mutation confirmation and must not mark mail read, change events, or alter files.

## Procedure

1. Compute the exact start and end of the requested week in the confirmed timezone.
2. Read meetings in that interval and group them by day with stable event identifiers.
3. Query Gmail for the unread count within the requested scope. Summarize categories only when requested; do not reproduce message bodies.
4. Fetch Drive metadata only for documents explicitly linked from selected events or requested by the user.
5. If connectors cannot complete the workflow, run:
   ```bash
   gws workflow +weekly-digest --format json
   ```
6. Label pagination, permission, and service gaps and distinguish an actual zero from an unavailable count.

## Safety and Errors

- Do not send mail, mark messages read, edit meetings, upload files, or change sharing.
- Never expose credentials or unrelated Gmail, Calendar, or Drive content.
- Resolve account, timezone, and week ambiguity before querying.
- Bound pagination and report partial data without silent retry loops.

## Output Contract

Return the week interval/timezone, meetings by day, unread count and exact query scope, requested linked-document metadata, route per service, counts, and all limitations. State that the digest is Read-only and no Workspace data was modified.
