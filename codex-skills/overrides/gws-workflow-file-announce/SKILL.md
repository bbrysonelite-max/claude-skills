---
name: "gws-workflow-file-announce"
description: "Google Workflow: Announce a Drive file in a Chat space."
---

# gws-workflow-file-announce

Resolve a Drive file and send one confirmed announcement to a Google Chat space.

## Codex Runtime

- **Dependencies:** connected Drive and Chat apps or gws CLI; Google Workspace credentials
- `connected Drive and Chat apps or gws CLI`
- `Google Workspace credentials`
- **Execution:** Operate directly in the main Codex agent.
- Prefer connected Google Drive and Chat capabilities; the `gws` CLI fallback is `gws workflow +file-announce`.
- Never print, log, or expose secret values.

## Inputs and Preflight

1. Require a Drive file ID, Chat space name such as `spaces/SPACE_ID`, account context, and optional message.
2. Check connected Drive and Chat capabilities first. If unavailable, confirm `gws` authentication and inspect the workflow help/schema.
3. Drive metadata lookup is Read-only and may proceed. Upload and Chat send operations are mutations.

## Procedure

1. Fetch only the file name, stable ID, URL, and access metadata needed to prepare the announcement.
2. Draft the announcement from the verified file name and URL, or use the requested custom message.
3. Present the exact Chat-space target, file, and message content. Obtain clear confirmation before sending.
4. Send once with connected Chat. Otherwise run:
   ```bash
   gws workflow +file-announce --file-id <ID> --space <SPACE> --message '<TEXT>'
   ```
5. If the user first requests a local-file upload, treat that as a separate mutation: confirm the destination and file, upload through connected Drive or `gws drive +upload`, then reconfirm the announcement content.
6. Verify the returned Chat message and report its stable identifier or URL.

## Safety and Errors

- Never upload or announce before explicit target/content confirmation.
- Do not announce a file the target audience cannot access; report access uncertainty instead of changing permissions implicitly.
- Never expose credential material or unrelated Drive/Chat content.
- After an uncertain send response, check the target space read-only before retrying.

## Output Contract

Return the file ID/name, Chat-space target, confirmed message, route used, message ID or URL, any upload result, and all access or delivery limitations. State clearly when nothing was sent.
