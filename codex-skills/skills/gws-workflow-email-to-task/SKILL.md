---
name: "gws-workflow-email-to-task"
description: "Google Workflow: Convert a Gmail message into a Google Tasks entry."
---

# gws-workflow-email-to-task

Read a Gmail message and create one confirmed Google Tasks entry from its subject and snippet.

## Codex Runtime

- **Dependencies:** connected Gmail and task apps or gws CLI; Google Workspace credentials
- `connected Gmail and task apps or gws CLI`
- `Google Workspace credentials`
- **Execution:** Operate directly in the main Codex agent.
- Prefer connected Gmail and Google Tasks capabilities; the `gws` CLI fallback is `gws workflow +email-to-task`.
- Never print, log, or expose secret values.

## Inputs and Preflight

1. Require a Gmail message ID and identify the account. Accept a task-list ID or use `@default` only after making that target explicit.
2. Check connected Gmail and Tasks capabilities first. If either required operation is unavailable, confirm `gws` authentication and inspect the workflow help/schema.
3. Reading the selected message is Read-only and may proceed without confirmation. Request only subject, snippet, sender, date, and stable identifiers.

## Procedure

1. Read the message through connected Gmail, or use a narrow Gmail CLI read as fallback.
2. Draft the task title from the subject and notes from the snippet. Do not silently include the full email, attachments, recipients, or unrelated thread content.
3. Present the exact task-list target and task content. Obtain clear confirmation before creation.
4. Create one task through connected Tasks when available. Otherwise run:
   ```bash
   gws workflow +email-to-task --message-id <ID> --tasklist <LIST_ID>
   ```
5. Read back the created task or inspect the CLI response and report its ID, title, and list.

## Safety and Errors

- Task creation is a mutation; never perform it before target/content confirmation.
- Never expose email bodies, tokens, or personal data beyond the requested task summary.
- If the message, account, or task list is ambiguous, stop and ask for the missing identifier.
- After an uncertain create response, query the task list before retrying to avoid duplicates.

## Output Contract

Return the source message ID, route used, confirmed task-list target and content, created task ID/title, and any omitted or blocked fields. State clearly when no task was created.
