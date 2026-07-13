---
name: "gws-workflow-standup-report"
description: "Google Workflow: Today's meetings + open tasks as a standup summary."
---

# gws-workflow-standup-report

Combine today's meetings and open tasks into a compact standup summary without changing either service.

## Codex Runtime

- **Dependencies:** connected Google Calendar and Google Tasks capabilities or gws CLI; Google Workspace credentials
- `connected Google Calendar and Google Tasks capabilities or gws CLI`
- `Google Workspace credentials`
- **Execution:** Operate directly in the main Codex agent.
- Prefer connected Google Calendar and Google Tasks capabilities; the `gws` CLI fallback is `gws workflow +standup-report`. Gmail is optional and used only for explicitly requested mail context.
- Never print, log, or expose secret values.

## Inputs and Preflight

1. Identify the account, timezone, calendar, task list, and the user's preferred standup format.
2. Check connected Calendar and Tasks capabilities first. If the required reads are unavailable, confirm `gws` authentication and inspect workflow help/schema.
3. This workflow is Read-only. It may proceed without mutation confirmation and must not complete, edit, or create tasks.

## Procedure

1. Read calendar events bounded to today in the confirmed timezone.
2. Read open tasks from the selected list, preserving due dates and completion state.
3. Use Gmail only if explicitly requested, with a narrow query and summarized results.
4. If connectors cannot complete the workflow, run:
   ```bash
   gws workflow +standup-report --format json
   ```
5. Deduplicate calendar/task references and render meetings in chronological order, followed by overdue, due-today, and undated open tasks.
6. Label service or permission gaps instead of implying the report is complete.

## Safety and Errors

- Do not modify meetings, tasks, or mail.
- Never expose credentials, full email bodies, or unrelated Workspace content.
- If timezone, calendar, or task-list scope is ambiguous, resolve it before reporting.
- Bound pagination and report truncation or partial service failure.

## Output Contract

Return the date/timezone, meeting agenda, categorized open tasks, any requested mail context, route per service, record counts, and coverage limitations. State that the report is Read-only and no Workspace data was modified.
