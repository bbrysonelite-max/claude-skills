---
name: "gws-workflow"
description: "Google Workflow: Cross-service productivity workflows."
---

# gws-workflow

Route cross-service Google productivity requests through the appropriate focused workflow.

## Codex Runtime

- **Dependencies:** connected Google Workspace apps or gws CLI; Google Workspace credentials
- `connected Google Workspace apps or gws CLI`
- `Google Workspace credentials`
- **Execution:** Operate directly in the main Codex agent.
- Prefer connected Workspace capabilities; the `gws` CLI fallback covers unavailable connectors.
- Never print, log, or expose secret values.

## Inputs and Preflight

1. Identify the requested workflow, account, date or message scope, target resource, and desired output.
2. Use the sibling Codex skill by name: `gws-workflow-standup-report`, `gws-workflow-meeting-prep`, `gws-workflow-email-to-task`, `gws-workflow-weekly-digest`, or `gws-workflow-file-announce`.
3. Check the required connected services first. If they are unavailable, verify `gws` authentication and inspect `gws workflow --help` plus the selected method schema.
4. Classify every step as Read-only or mutating. Read-only calls may proceed; mutations require confirmed target and content.

## Procedure

1. Select the narrowest sibling workflow and follow its input, confirmation, and output contract.
2. Use connected Gmail, Drive, Calendar, Tasks, or Chat operations for each covered step.
3. Fall back only for uncovered steps with `gws workflow +<workflow>`, using schema-derived flags.
4. Keep cross-service identifiers associated with their service and account. Do not infer IDs from display names when ambiguity exists.
5. Before creating a task, sending or announcing a message, or uploading a file, show the exact target and content and obtain clear confirmation.
6. Return a combined result that distinguishes connector results, CLI fallback results, skipped mutations, and partial failures.

## Safety and Errors

- Never expose credentials or broader Workspace content than the request requires.
- Do not substitute another account, calendar, task list, file, or Chat space when a target is ambiguous.
- Do not retry a mutation after an uncertain response until current state is checked read-only.
- If no sibling workflow fits, use the rules in `gws-shared` and state the custom plan before acting.

## Output Contract

Return the selected sibling skill, route per service, Read-only evidence gathered, confirmed mutation target/content if any, resulting resource IDs or URLs, and all blocked or partial steps.
