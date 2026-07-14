---
name: "gws-workflow-meeting-prep"
description: "Google Workflow: Prepare for your next meeting: agenda, attendees, and linked docs."
---

# gws-workflow-meeting-prep

Prepare a concise evidence-based brief for the next calendar meeting without modifying Workspace data.

## Codex Runtime

- **Dependencies:** connected Gmail, Calendar, and Drive apps or gws CLI; Google Workspace credentials
- `connected Gmail, Calendar, and Drive apps or gws CLI`
- `Google Workspace credentials`
- **Execution:** Operate directly in the main Codex agent.
- Prefer connected Calendar, Gmail, and Google Drive capabilities; the `gws` CLI fallback is `gws workflow +meeting-prep`.
- Never print, log, or expose secret values.

## Inputs and Preflight

1. Identify the account, calendar ID (default `primary`), current timezone, and optional meeting filter.
2. Check connected Calendar, Gmail, and Drive capabilities first. If the required reads are unavailable, confirm `gws` authentication and inspect the workflow help/schema.
3. This workflow is Read-only. It may proceed without mutation confirmation, but request only data needed for the brief.

## Procedure

1. Read upcoming events and select the next unambiguous meeting in the requested calendar and timezone.
2. Gather the event title, time, organizer, attendees, description, conference link, and linked Drive documents through connected services.
3. Search Gmail only when the user requests related correspondence or when a stable event identifier clearly scopes the query. Summarize rather than reproducing sensitive messages.
4. If connectors cannot complete the workflow, run:
   ```bash
   gws workflow +meeting-prep --calendar <CALENDAR_ID>
   ```
5. Separate verified agenda material from inferred preparation notes and name missing access.

## Safety and Errors

- Do not edit events, invite attendees, send email, change file permissions, or upload anything.
- Never expose credentials or unrelated attendee, email, or Drive content.
- If multiple meetings are equally plausible, ask the user to select one before retrieving broader context.
- Report connector, permission, timezone, and fallback limitations explicitly.

## Output Contract

Return the selected event ID/title/time/timezone, attendee and agenda summary, linked documents with access status, scoped email context if requested, route used, and all missing or inferred information. State that no Workspace data was modified.
