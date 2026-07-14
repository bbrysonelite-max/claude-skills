# Inquiry Tree — JSON schema & resume mechanics

The audit trail (spec §7.2). One file per run: `trees/<industry>-<date>.json`. Written
incrementally — every time a node becomes `grounded`, the file is re-saved.

## Shape

```json
{
  "vertical": "string — the seed vertical",
  "seed": "string — verbatim operator seed",
  "date": "YYYY-MM-DD",
  "config_snapshot": { "depth_cap": 4, "confidence_threshold": "medium", "confirm_mode": "confirm" },
  "root_id": "n1",
  "nodes": {
    "n1": {
      "id": "n1",
      "subject": "the golden lead for <vertical>",
      "depth": 0,
      "parent_id": null,
      "answers": {
        "who":   { "value": "string|null", "status": "known|needs-research|grounded", "evidence": [], "child_ids": [] },
        "what":  { "value": "string|null", "status": "known|needs-research|grounded", "evidence": [], "child_ids": [] },
        "when":  { "value": "string|null", "status": "known|needs-research|grounded", "evidence": [], "child_ids": [] },
        "where": { "value": "string|null", "status": "known|needs-research|grounded", "evidence": [], "child_ids": [] },
        "why":   { "value": "string|null", "status": "known|needs-research|grounded", "evidence": [], "child_ids": [] },
        "how":   { "value": "string|null", "status": "known|needs-research|grounded", "evidence": [], "child_ids": [] }
      }
    }
  },
  "verdict": { "decision": "go|no-go|pending", "confidence": "low|medium|high", "match_statement": "string|null" }
}
```

An **evidence** entry: `{ "source": "string", "link": "string|null", "quote": "string|null", "number": "string|null" }`.

A child node uses the same node shape; its `parent_id` is the spawning node's id and its
`subject` is the specific Who/What/Where that the parent surfaced.

## Status meanings

- `known` — supplied/confirmed by the operator.
- `needs-research` — the skill must dispatch a research subagent to draft it.
- `grounded` — proven, with at least one `evidence` entry attached. The buyer branch is only
  `grounded` with **money-in-hand** evidence.

## Resume

To resume an interrupted run, the operator re-invokes Blueprint with the same vertical. The skill
loads the existing `trees/<industry>-<date>.json`, then continues from the **first node whose
answers are not all `grounded` or capped**. Nothing already `grounded` is re-researched.
