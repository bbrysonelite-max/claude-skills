# Agents Catalog — what's available to Brent, and the rules

A reference for the **subagents** available in this environment (`~/.claude/agents/`),
how they're meant to be used, and the rules that govern them. This is a map, not the
source of truth: for GSD, the canonical rules live in `~/.claude/gsd-core/` + the guard
hooks — this doc summarizes and points there.

Three buckets: **(1) your authored agents**, **(2) the GSD team** (installed framework),
**(3) plugin/built-in agent types** (not files you own).

---

## 1. Your authored agents (2)

| Agent | What it does | Key rules |
|---|---|---|
| **`doc-keeper`** | Project-AGNOSTIC living-docs reconciler. Discovers whatever docs a project keeps (README/CHANGELOG/status/ADRs/index) and reconciles them to reality via ONE docs PR. | Docs only, never code. Never push the default branch; one PR; never merges. Evidence-grounded. |
| **`tiger-doc-keeper`** | The Tiger Claw specialist — knows SOTU/NEXT_SESSION/PROGRESS/TO-DO/VERIFIED/ADRs + the repo's doc-CI guards + SACRED_WIRING. | Same as above, Tiger-scoped. Use this one for `tiger-claw-v4-core`; use `doc-keeper` everywhere else. |

These are the only hand-authored agents. Everything below is installed.

---

## 2. The GSD team (33 agents) — an installed framework

**GSD ("Get Stuff Done")** is a complete installed system: the `gsd-*` agents +
`~/.claude/gsd-core/` (≈90 workflows) + guard hooks. **You do not spawn `gsd-*` agents
by hand** — a `/gsd-*` orchestrator command spawns the right ones in sequence and tracks
state under `.planning/`. The catalog below maps each agent to the command that drives it.

**Plan / roadmap** — `/gsd-new-project`, `/gsd-new-milestone`, `/gsd-plan-phase`
- `gsd-project-researcher` — research the domain ecosystem before roadmapping
- `gsd-research-synthesizer` — synthesize parallel research into one summary
- `gsd-roadmapper` — requirements → phases with goal-backward success criteria

**Discuss / plan a phase** — `/gsd-discuss-phase`, `/gsd-plan-phase`
- `gsd-phase-researcher` — how to implement a phase (produces RESEARCH.md)
- `gsd-pattern-mapper` — map new files to existing codebase patterns
- `gsd-assumptions-analyzer` — surface assumptions with evidence
- `gsd-advisor-researcher` — research a single gray-area decision → comparison table
- `gsd-planner` — executable phase plan; `gsd-plan-checker` — verify the plan reaches the goal

**Execute** — `/gsd-execute-phase`
- `gsd-executor` — execute the plan with atomic commits + checkpoints
- `gsd-codebase-mapper` — map structure/architecture for a focus area
- `gsd-verifier` — goal-backward check that the phase delivered what it promised

**Review / audit** — `/gsd-code-review`, `/gsd-ui-review`, `/gsd-secure-phase`, `/gsd-eval-review`
- `gsd-code-reviewer` → `gsd-code-fixer` — find then fix bugs/security/quality
- `gsd-ui-auditor`, `gsd-ui-checker` — visual/design-contract audits
- `gsd-security-auditor` — verify threat mitigations exist in code
- `gsd-eval-auditor` — audit an AI phase's eval coverage
- `gsd-integration-checker`, `gsd-nyquist-auditor` — cross-phase E2E + requirement-coverage checks

**Debug** — `/gsd-debug`
- `gsd-debugger`, `gsd-debug-session-manager` — scientific-method debugging + the cycle loop

**AI integration** — `/gsd-ai-integration-phase`
- `gsd-framework-selector`, `gsd-ai-researcher`, `gsd-domain-researcher`, `gsd-eval-planner`

**Docs / mapping** — `/gsd-ingest-docs`, `/gsd-docs-update`, `/gsd-map-codebase`
- `gsd-doc-classifier`, `gsd-doc-synthesizer` — classify + consolidate planning docs
- `gsd-doc-writer`, `gsd-doc-verifier` — write docs + verify claims against live code
- `gsd-intel-updater` — write structured intel to `.planning/intel/`
- `gsd-user-profiler` — score a developer profile from session history

### GSD operating rules (grounded in gsd-core + hooks)
- **Orchestrated, not manual.** Run `/gsd-*` commands; let them spawn the agents. The full
  command list is `~/.claude/gsd-core/workflows/` (new-project, plan-phase, execute-phase,
  code-review, debug, ship, …).
- **Enforced by guard hooks** (`~/.claude/hooks/gsd-*`): `workflow-guard` (soft-advises
  against edits outside a GSD workflow), `read-guard` + `read-injection-scanner`,
  `worktree-path-guard`, `validate-commit`, `phase-boundary`, `context-monitor`.
- **State lives in `.planning/`** (roadmap, phases, intel, research) — agents read/write there.
- **Authoritative rules = the GSD source**, not this doc. When in doubt, read the workflow file.

---

## 3. Plugin / built-in agent types (available, not files you own)

Provided by Claude Code / plugins, usable via the Agent tool but not in `~/.claude/agents/`:
`Explore`, `Plan`, `general-purpose`, `code-simplifier`, `claude-code-guide`,
`statusline-setup`, the `understand-anything:*` set, and the `vercel:*` set.

---

## Cross-cutting rules (Brent's — apply to EVERY agent you spawn)

- **Ground-truth first** — agents establish what's literally true (run it / read the bytes), label GROUNDED vs UNVERIFIED. Never report "done" from a return code.
- **Never push to `main`/`master`** — branch → PR → merge on Brent's explicit go. Holds for every repo, including backups.
- **Three-agent rule** — the author never tests or reviews its own work; spawn independent test + review before merge.
- **Secret-scan before any commit**; never echo a key value; reference keys by name.
- **Worktree isolation** for agents that mutate files in parallel.
- **Docs-only agents never touch code** (doc-keeper / tiger-doc-keeper / gsd-doc-*).

_Backup: this catalog + the agent definitions are mirrored to the private `claude-skills`
repo by the librarian (`skills-librarian/scripts/backup.sh`), which also snapshots
`~/.claude/agents/` into `.agents-backup/`._
