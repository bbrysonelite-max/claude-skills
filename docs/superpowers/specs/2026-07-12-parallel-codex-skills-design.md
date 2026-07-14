# Parallel Codex Skills Collection

## Goal

Create Codex equivalents for all 51 existing Claude skills without changing, moving, or renaming any existing Claude skill directory. Promote seven broadly useful parked agent definitions into standalone Codex skills.

## Repository Layout

Keep the current repository root as the Claude collection. Add a parallel tree:

```text
claude-skills/
├── <existing Claude skill folders, unchanged>
├── .agents-backup/                  # unchanged source archive
└── codex-skills/
    ├── manifest.yaml
    ├── scripts/
    │   ├── build.py
    │   ├── install.py
    │   └── validate.py
    └── skills/
        ├── <51 adapted equivalents>/
        └── <7 promoted skills>/
```

Every generated skill contains `SKILL.md`, copied supporting resources when needed, and `agents/openai.yaml`.

## Source Protection

- Treat the 51 existing skill directories and `.agents-backup/` as read-only inputs.
- Record source hashes before generation and verify them afterward.
- Never rewrite root skill frontmatter for Codex compatibility.
- Preserve the existing uncommitted `.gitignore` change.
- Restrict new repository changes to `codex-skills/` and this design/plan documentation.

## Conversion Classes

Each source skill receives one manifest classification:

- `native`: content already works in Codex; normalize only copied frontmatter and UI metadata.
- `adapted`: replace Claude-specific tool names, paths, orchestration, or browser behavior in the copied version.
- `dependency-required`: the workflow is Codex-compatible but relies on an external CLI, MCP server, credentials, repository, or local service. Include a preflight and a useful blocked-state response.

No source skill is silently dropped. The manifest records source path, output path, conversion class, required dependencies, and adaptation notes.

## Runtime Adaptation

- Replace Claude tool-name instructions with Codex capabilities such as shell execution, `apply_patch`, web access, connected apps, browser automation, and collaboration tools when allowed.
- Replace mandatory Claude subagent dispatch with a direct main-agent workflow; allow Codex delegation only when the active environment permits it.
- Change Codex session-writing workflows to `.codex/sessions/` while allowing read-only discovery of historical `.claude/sessions/` evidence.
- Adapt Claude skill-library maintenance to `~/.codex/skills` and the parallel collection.
- Prefer connected Gmail and Google Drive apps for Google Workspace workflows; retain `gws` only as a documented fallback.
- Prefer the Codex browser skill or agent-browser for page inspection instead of the Claude gstack browser binary.
- Preserve actual product names such as `claude-memory` and GitNexus where they identify external tools, and add availability checks plus CLI/MCP fallbacks.
- Keep user-specific business rules, safety constraints, output contracts, scripts, references, and assets unless they depend on Claude-only behavior.

## Promoted Parked Skills

Convert these archived agent capabilities into standalone, GSD-independent Codex skills:

1. `assumptions-audit`
2. `codebase-pattern-mapping`
3. `documentation-claim-verification`
4. `integration-flow-audit`
5. `requirements-coverage-audit`
6. `threat-mitigation-audit`
7. `ai-evaluation-audit`

Remove dependencies on GSD orchestrators, Claude slash commands, fixed `.planning/` files, and exact Claude tool names. Preserve their evidence standards and structured outputs.

## Build And Installation

- Use a deterministic build script with an explicit per-skill adaptation table.
- Fail generation on an unknown skill, missing resource, invalid frontmatter, duplicate output name, or unresolved Claude-only instruction.
- Install by creating managed symlinks from `~/.codex/skills/<name>` to `codex-skills/skills/<name>`.
- Never replace a pre-existing non-managed personal skill. Report collisions for explicit resolution.
- Make repeated build and install runs idempotent.

## Validation

1. Confirm exactly 51 source skills were discovered and 58 Codex skills were produced.
2. Verify all source hashes match the pre-build snapshot.
3. Validate every `SKILL.md` against Codex skill naming and frontmatter requirements.
4. Validate every `agents/openai.yaml` and ensure its default prompt names the skill.
5. Verify copied local resource links and executable script references resolve.
6. Scan copied skills for prohibited Claude-only tool instructions, hard-coded `~/.claude/skills` execution paths, and required Claude subagent calls.
7. Run syntax checks for copied Python, shell, and JavaScript resources where the relevant runtime is present.
8. Run installer idempotence and collision tests in a temporary skill home before installing personally.
9. Confirm the personal Codex skill directory exposes all generated skills without altering existing unrelated skills.

External services, credentials, live production systems, paid APIs, and destructive workflows are not invoked during collection validation.

## Deliverables

- A version-controlled parallel Codex collection in `codex-skills/`.
- A machine-readable compatibility manifest.
- Deterministic build, validation, and installation scripts.
- Fifty-one source-equivalent skills and seven promoted parked skills.
- A validation report listing fully runnable skills and dependency-gated skills.
