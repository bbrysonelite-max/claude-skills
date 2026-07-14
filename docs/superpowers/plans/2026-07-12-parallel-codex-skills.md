# Parallel Codex Skills Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build, validate, and install a parallel collection of 51 Codex equivalents plus seven promoted standalone skills without changing any existing Claude skill.

**Architecture:** A standard-library Python toolchain reads a JSON-compatible `manifest.yaml`, copies source resources into `codex-skills/skills`, normalizes Codex metadata, and applies explicit per-skill adapters. Separate validation and installation programs enforce source immutability, runtime compatibility, resource integrity, collision safety, and idempotent symlink installation.

**Tech Stack:** Python 3.11+ standard library, `unittest`, Markdown/YAML skill files, Git, shell syntax checks, Codex `quick_validate.py` through an isolated `uv` environment.

---

## File Map

- `codex-skills/manifest.yaml`: JSON-compatible YAML inventory for 51 source conversions and seven promoted skills.
- `codex-skills/source-hashes.json`: deterministic hashes of all protected Claude source files.
- `codex-skills/scripts/common.py`: manifest, frontmatter, hashing, path, and metadata helpers.
- `codex-skills/scripts/adapt.py`: generic rewrites and explicit adapter registry.
- `codex-skills/scripts/build.py`: deterministic output generation and stale-output cleanup.
- `codex-skills/scripts/validate.py`: collection-wide schema, compatibility, resource, syntax, and immutability validation.
- `codex-skills/scripts/install.py`: collision-safe managed symlink installer.
- `codex-skills/overrides/<skill>/SKILL.md`: complete Codex workflow replacement only where mechanical adaptation is unsafe.
- `codex-skills/promoted/<skill>/SKILL.md`: seven standalone skills derived from archived agent definitions.
- `codex-skills/skills/<skill>/`: generated, installable skill output.
- `codex-skills/tests/`: standard-library unit and integration tests.
- `codex-skills/VALIDATION.md`: generated compatibility and dependency report.

## Task 1: Protect The Claude Sources

**Files:**
- Create: `codex-skills/tests/test_source_protection.py`
- Create: `codex-skills/scripts/common.py`
- Create: `codex-skills/source-hashes.json`

- [ ] **Step 1: Write the failing source-discovery and hash test**

```python
from pathlib import Path
import json
import unittest

from scripts.common import discover_source_skills, hash_protected_sources


ROOT = Path(__file__).resolve().parents[2]


class SourceProtectionTests(unittest.TestCase):
    def test_discovers_exactly_51_root_skills(self):
        skills = discover_source_skills(ROOT)
        self.assertEqual(51, len(skills))
        self.assertEqual("agent-reach", skills[0].name)
        self.assertEqual("whitelabel-radar", skills[-1].name)

    def test_hash_snapshot_matches_current_sources(self):
        expected = json.loads((ROOT / "codex-skills/source-hashes.json").read_text())
        self.assertEqual(expected, hash_protected_sources(ROOT))
```

- [ ] **Step 2: Run the test and verify it fails because `scripts.common` does not exist**

Run: `cd /Users/brentbryson/claude-skills/codex-skills && python3 -m unittest tests.test_source_protection -v`

Expected: `ModuleNotFoundError: No module named 'scripts.common'`.

- [ ] **Step 3: Implement source discovery and deterministic hashing**

`discover_source_skills(root)` must inspect only direct children of the repository root, require `SKILL.md`, exclude hidden directories, `codex-skills`, and `docs`, and return paths sorted by folder name. `hash_protected_sources(root)` must hash every file below those 51 directories plus `.agents-backup/`, using repository-relative POSIX paths and SHA-256 byte hashes.

```python
def hash_protected_sources(root: Path) -> dict[str, str]:
    paths = []
    for skill in discover_source_skills(root):
        paths.extend(p for p in skill.rglob("*") if p.is_file())
    backup = root / ".agents-backup"
    paths.extend(p for p in backup.rglob("*") if p.is_file())
    return {
        p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted(paths)
    }
```

- [ ] **Step 4: Generate the baseline snapshot and rerun the test**

Run: `python3 -c 'from pathlib import Path; import json; from scripts.common import hash_protected_sources; r=Path("..").resolve(); Path("source-hashes.json").write_text(json.dumps(hash_protected_sources(r), indent=2)+"\n")'`

Run: `python3 -m unittest tests.test_source_protection -v`

Expected: two tests pass and the snapshot contains paths from all 51 folders plus `.agents-backup/`.

- [ ] **Step 5: Commit**

```bash
git add codex-skills/scripts/common.py codex-skills/tests/test_source_protection.py codex-skills/source-hashes.json
git commit -m "test: protect Claude skill sources"
```

## Task 2: Define And Parse The Compatibility Manifest

**Files:**
- Create: `codex-skills/tests/test_manifest.py`
- Create: `codex-skills/manifest.yaml`
- Modify: `codex-skills/scripts/common.py`

- [ ] **Step 1: Write failing manifest-contract tests**

```python
class ManifestTests(unittest.TestCase):
    def test_manifest_has_51_sources_and_7_promoted_skills(self):
        manifest = load_manifest(ROOT / "manifest.yaml")
        self.assertEqual(51, len(manifest.sources))
        self.assertEqual(7, len(manifest.promoted))
        self.assertEqual(58, len({entry.output for entry in manifest.entries}))

    def test_all_source_folders_are_accounted_for(self):
        manifest = load_manifest(ROOT / "manifest.yaml")
        discovered = {p.name for p in discover_source_skills(REPO)}
        self.assertEqual(discovered, {entry.source for entry in manifest.sources})

    def test_classes_and_dependency_lists_are_valid(self):
        manifest = load_manifest(ROOT / "manifest.yaml")
        for entry in manifest.entries:
            self.assertIn(entry.conversion, {"native", "adapted", "dependency-required"})
            self.assertIsInstance(entry.dependencies, tuple)
```

- [ ] **Step 2: Run the tests and verify failure on the missing manifest loader**

Run: `python3 -m unittest tests.test_manifest -v`

Expected: import or attribute failure for `load_manifest`.

- [ ] **Step 3: Implement immutable manifest dataclasses and JSON-compatible YAML parsing**

Use `json.loads()` because JSON is a valid YAML subset. Reject unknown top-level keys, unknown entry keys, missing fields, duplicate source names, duplicate output names, unsafe names, and entries whose source path does not exist.

```python
@dataclass(frozen=True)
class SkillEntry:
    source: str | None
    promoted_from: str | None
    output: str
    conversion: str
    dependencies: tuple[str, ...]
    notes: str


@dataclass(frozen=True)
class Manifest:
    sources: tuple[SkillEntry, ...]
    promoted: tuple[SkillEntry, ...]

    @property
    def entries(self) -> tuple[SkillEntry, ...]:
        return self.sources + self.promoted
```

- [ ] **Step 4: Add all 51 source entries and seven promoted entries**

The 51 source names must be exactly:

```text
agent-reach, allsup-leads-ssdi, allsup-leads-veterans, blind-spots-audit,
blueprint, claude-memory-debug, claude-memory-index, claude-memory-search,
claude-memory-status, closing-ritual, cloud-run-reauth, context-keeper,
desktop-delivery, doc-keeper, failure-modes, gitnexus-cli,
gitnexus-debugging, gitnexus-exploring, gitnexus-guide,
gitnexus-impact-analysis, gitnexus-pr-review, gitnexus-refactoring,
ground-truth, gws-shared, gws-workflow, gws-workflow-email-to-task,
gws-workflow-file-announce, gws-workflow-meeting-prep,
gws-workflow-standup-report, gws-workflow-weekly-digest, here-now,
intro-page, last30days, mine, network-reactivator, page-rethink,
production-gate-audit, refine, ship-it, signal-mine, skill-miner,
skills-librarian, the-rebuild, tiger-doc-keeper, tiger-leader-hunt,
tiger-whitepaper, tigerclaw-daily-checks, truth-keeper, two-brents-brand,
vault-hygiene, whitelabel-radar
```

The promoted outputs must be `assumptions-audit`, `codebase-pattern-mapping`, `documentation-claim-verification`, `integration-flow-audit`, `requirements-coverage-audit`, `threat-mitigation-audit`, and `ai-evaluation-audit`.

- [ ] **Step 5: Run tests and commit**

Run: `python3 -m unittest tests.test_manifest -v`

Expected: all manifest tests pass.

```bash
git add codex-skills/manifest.yaml codex-skills/scripts/common.py codex-skills/tests/test_manifest.py
git commit -m "feat: define Codex skill compatibility manifest"
```

## Task 3: Build Native Copies And Codex Metadata

**Files:**
- Create: `codex-skills/tests/test_build.py`
- Create: `codex-skills/scripts/build.py`
- Modify: `codex-skills/scripts/common.py`

- [ ] **Step 1: Write failing build tests using a temporary repository fixture**

```python
def test_build_normalizes_frontmatter_and_copies_resources(self):
    source = self.repo / "sample"
    source.mkdir()
    (source / "SKILL.md").write_text(
        "---\nname: sample\nversion: 2\ndescription: Use when testing builds.\n---\n\n# Sample\n"
    )
    (source / "scripts").mkdir()
    (source / "scripts/run.py").write_text("print('ok')\n")
    build_collection(self.repo, self.manifest, self.output)
    skill = (self.output / "sample/SKILL.md").read_text()
    self.assertTrue(skill.startswith("---\nname: sample\ndescription:"))
    self.assertNotIn("version:", skill.split("---", 2)[1])
    self.assertTrue((self.output / "sample/scripts/run.py").is_file())
    self.assertTrue((self.output / "sample/agents/openai.yaml").is_file())
```

- [ ] **Step 2: Run and verify the build test fails because `build_collection` is absent**

Run: `python3 -m unittest tests.test_build -v`

Expected: import failure for `scripts.build`.

- [ ] **Step 3: Implement frontmatter extraction and normalized skill rendering**

Support plain, single-quoted, double-quoted, folded (`>`), and literal (`|`) descriptions. Emit only `name` and `description` in generated `SKILL.md` frontmatter. Reject a missing description or a source `name` that differs from its folder.

- [ ] **Step 4: Implement deterministic resource copying**

Copy files and directories except `.git`, `.DS_Store`, source `agents/openai.yaml`, cache directories, bytecode, logs, and runtime state directories. Preserve executable bits. Delete only the generated output directory before a clean rebuild; never delete or write a source directory.

- [ ] **Step 5: Generate `agents/openai.yaml`**

Generate only:

```yaml
interface:
  display_name: "Sample"
  short_description: "Use Sample for the workflow described by this skill."
  default_prompt: "Use $sample to complete this request."
```

Derive `display_name` from the output name, cap `short_description` at 100 characters, and ensure `default_prompt` includes `$<output-name>`.

- [ ] **Step 6: Run build tests and commit**

Run: `python3 -m unittest tests.test_build -v`

Expected: frontmatter, resource, metadata, executable-bit, and clean-rebuild tests pass.

```bash
git add codex-skills/scripts/build.py codex-skills/scripts/common.py codex-skills/tests/test_build.py
git commit -m "feat: build normalized Codex skill copies"
```

## Task 4: Add The Explicit Runtime Adapter Layer

**Files:**
- Create: `codex-skills/tests/test_adapt.py`
- Create: `codex-skills/scripts/adapt.py`
- Modify: `codex-skills/scripts/build.py`

- [ ] **Step 1: Write failing adapter tests**

Test that adapters are explicit, do not run against undeclared skills, leave product names intact, and replace only operational Claude coupling.

```python
def test_context_keeper_writes_codex_sessions_but_reads_legacy_evidence(self):
    result = adapt_text("context-keeper", SOURCE_TEXT)
    self.assertIn(".codex/sessions/", result)
    self.assertIn("historical `.claude/sessions/`", result)

def test_claude_memory_product_name_is_preserved(self):
    result = adapt_text("claude-memory-search", MEMORY_TEXT)
    self.assertIn("claude-memory", result)

def test_unknown_adapter_is_rejected(self):
    with self.assertRaises(KeyError):
        adapt_text("not-in-manifest", "text")
```

- [ ] **Step 2: Run and verify adapter tests fail**

Run: `python3 -m unittest tests.test_adapt -v`

Expected: import failure for `scripts.adapt`.

- [ ] **Step 3: Implement generic safe rewrites**

Generic rewrites may normalize instructional phrases such as “Bash tool” to “shell execution” and “Read tool” to “file reading,” but must not replace `Claude` globally. Use exact strings and compiled regular expressions with expected replacement counts. Fail when an expected source pattern is missing so upstream drift is visible.

- [ ] **Step 4: Implement named adapter groups**

Create explicit adapters for:

```text
session paths: context-keeper, closing-ritual, doc-keeper, tiger-doc-keeper
library paths: skill-miner, skills-librarian
browser: page-rethink, intro-page
connected apps: gws-shared and all six gws-workflow skills
delegation: doc-keeper, tiger-doc-keeper, agent-reach
product dependencies: four claude-memory skills and seven gitnexus skills
cross-skill paths: allsup-leads-ssdi, allsup-leads-veterans, mine,
  refine, signal-mine, whitelabel-radar, tiger-leader-hunt
```

For each group, add dependency preflight text and a blocked-state instruction where applicable. Google Workspace copies must prefer connected Gmail/Drive tools and retain `gws` as fallback. Browser copies must reference the installed `browser-use:browser` or `vercel:agent-browser` skill instead of the gstack binary.

- [ ] **Step 5: Integrate adapters into the build and rerun tests**

Run: `python3 -m unittest tests.test_adapt tests.test_build -v`

Expected: all adapter and build tests pass.

- [ ] **Step 6: Commit**

```bash
git add codex-skills/scripts/adapt.py codex-skills/scripts/build.py codex-skills/tests/test_adapt.py
git commit -m "feat: adapt Claude workflows to Codex runtime"
```

## Task 5: Add Complete Overrides For Unsafe Mechanical Conversions

**Files:**
- Create: `codex-skills/overrides/context-keeper/SKILL.md`
- Create: `codex-skills/overrides/doc-keeper/SKILL.md`
- Create: `codex-skills/overrides/tiger-doc-keeper/SKILL.md`
- Create: `codex-skills/overrides/skill-miner/SKILL.md`
- Create: `codex-skills/overrides/skills-librarian/SKILL.md`
- Create: `codex-skills/overrides/page-rethink/SKILL.md`
- Create: `codex-skills/overrides/gws-shared/SKILL.md`
- Create: `codex-skills/overrides/gws-workflow/SKILL.md`
- Create: `codex-skills/overrides/gws-workflow-email-to-task/SKILL.md`
- Create: `codex-skills/overrides/gws-workflow-file-announce/SKILL.md`
- Create: `codex-skills/overrides/gws-workflow-meeting-prep/SKILL.md`
- Create: `codex-skills/overrides/gws-workflow-standup-report/SKILL.md`
- Create: `codex-skills/overrides/gws-workflow-weekly-digest/SKILL.md`
- Modify: `codex-skills/tests/test_build.py`
- Modify: `codex-skills/scripts/build.py`

- [ ] **Step 1: Add failing tests that require overrides for the 13 listed skills**

Assert that every override output retains the source trigger description, contains a `## Codex Runtime` section, and has none of these required operational patterns: `Agent(`, `AskUserQuestion`, `Task(`, `$HOME/.claude/skills/gstack`, or “use the Write tool.”

- [ ] **Step 2: Run tests and verify they fail on missing override files**

Run: `python3 -m unittest tests.test_build.BuildOverrideTests -v`

Expected: failure listing 13 missing overrides.

- [ ] **Step 3: Write concise complete Codex workflows**

Each override must preserve the source skill’s domain rules and output contract while replacing only runtime behavior. `doc-keeper` variants perform the workflow directly and may delegate only when permitted. `skill-miner` reads Codex JSONL session history without modifying it. `skills-librarian` audits `~/.codex/skills` and the parallel manifest. Google Workspace skills use connector tools first and make mutation confirmation requirements explicit.

- [ ] **Step 4: Teach the build to prefer an override after resource copying**

An override replaces only generated `SKILL.md`; supporting source scripts/references/assets remain copied. Reject an override whose frontmatter name differs from the manifest output.

- [ ] **Step 5: Run tests and commit**

Run: `python3 -m unittest tests.test_build tests.test_adapt -v`

Expected: override contract and prior build tests pass.

```bash
git add codex-skills/overrides codex-skills/scripts/build.py codex-skills/tests/test_build.py
git commit -m "feat: add Codex-native workflow overrides"
```

## Task 6: Promote Seven Parked Agent Capabilities

**Files:**
- Create: `codex-skills/promoted/assumptions-audit/SKILL.md`
- Create: `codex-skills/promoted/codebase-pattern-mapping/SKILL.md`
- Create: `codex-skills/promoted/documentation-claim-verification/SKILL.md`
- Create: `codex-skills/promoted/integration-flow-audit/SKILL.md`
- Create: `codex-skills/promoted/requirements-coverage-audit/SKILL.md`
- Create: `codex-skills/promoted/threat-mitigation-audit/SKILL.md`
- Create: `codex-skills/promoted/ai-evaluation-audit/SKILL.md`
- Create: `codex-skills/tests/test_promoted.py`
- Modify: `codex-skills/scripts/build.py`

- [ ] **Step 1: Write failing promoted-skill contract tests**

Require seven files, Codex-valid names/descriptions, evidence citation rules, direct invocation without a GSD orchestrator, no mandatory `.planning/` paths, and no Claude tool names.

- [ ] **Step 2: Run tests and verify seven missing-skill failures**

Run: `python3 -m unittest tests.test_promoted -v`

Expected: seven missing file failures.

- [ ] **Step 3: Initialize and write the seven skills**

Use the Codex skill initializer for each promoted skill, then replace the template with a concise standalone workflow. Preserve these source invariants:

```text
assumptions-audit: evidence, confidence, consequence if wrong
codebase-pattern-mapping: closest analogs, conventions, deviation risks
documentation-claim-verification: claim-by-claim PASS/FAIL/UNVERIFIABLE
integration-flow-audit: complete user flow, boundary contracts, failure propagation
requirements-coverage-audit: requirement-to-test matrix and executable proof
threat-mitigation-audit: mitigation presumed absent until implementation evidence
ai-evaluation-audit: planned dimension scored COVERED/PARTIAL/MISSING
```

- [ ] **Step 4: Make the builder copy promoted sources and generate UI metadata**

Promoted inputs use `promoted_from` in the manifest for provenance but do not load the full archived agent at runtime.

- [ ] **Step 5: Run tests and commit**

Run: `python3 -m unittest tests.test_promoted tests.test_build -v`

Expected: promoted contracts and build tests pass.

```bash
git add codex-skills/promoted codex-skills/scripts/build.py codex-skills/tests/test_promoted.py
git commit -m "feat: promote high-value archived agents to Codex skills"
```

## Task 7: Validate The Generated Collection

**Files:**
- Create: `codex-skills/tests/test_validate.py`
- Create: `codex-skills/scripts/validate.py`
- Create: `codex-skills/VALIDATION.md`

- [ ] **Step 1: Write failing validation tests**

```python
def test_validation_rejects_claude_only_operational_instruction(self):
    skill = fixture_skill("Use the AskUserQuestion tool now.")
    result = validate_skill(skill)
    self.assertIn("AskUserQuestion", result.errors[0])

def test_validation_accepts_historical_claude_reference(self):
    skill = fixture_skill("Read historical `.claude/sessions/` as evidence.")
    self.assertEqual([], validate_skill(skill).errors)

def test_full_collection_has_58_valid_skills(self):
    report = validate_collection(REPO)
    self.assertEqual(58, report.skill_count)
    self.assertEqual([], report.errors)
```

- [ ] **Step 2: Run and verify tests fail because validation is absent**

Run: `python3 -m unittest tests.test_validate -v`

Expected: import failure for `scripts.validate`.

- [ ] **Step 3: Implement structural and compatibility validation**

Validate count, folder/name match, two-field frontmatter, description length, `agents/openai.yaml`, default prompt token, duplicate names, local Markdown links, referenced scripts, manifest/output parity, source hashes, prohibited operational phrases, and dependency-preflight presence.

- [ ] **Step 4: Implement resource syntax checks**

Run `python3 -m py_compile` for copied Python, `bash -n` for shell scripts, and `node --check` for `.js`, `.cjs`, and `.mjs` files when Node is available. Exclude vendored dependencies, build outputs, and fixture data. Report every checked path and failure.

- [ ] **Step 5: Run the Codex validator in an isolated uv environment**

Run for each generated skill:

```bash
uv run --with pyyaml python /Users/brentbryson/.codex/skills/.system/skill-creator/scripts/quick_validate.py <skill-path>
```

Cache the environment through `uv`; do not install PyYAML into the system interpreter.

- [ ] **Step 6: Generate `VALIDATION.md`**

The report must list total skills, source immutability result, structural result, syntax-check counts, installability, and a table of every `dependency-required` skill with its preflight dependency names. It must contain observed results, not claims copied from the manifest.

- [ ] **Step 7: Run tests and commit**

Run: `python3 -m unittest discover -s tests -v`

Run: `python3 scripts/build.py && python3 scripts/validate.py`

Expected: all tests pass, 58 skills validate, and source hashes match.

```bash
git add codex-skills/scripts/validate.py codex-skills/tests/test_validate.py codex-skills/VALIDATION.md codex-skills/skills
git commit -m "feat: generate and validate 58 Codex skills"
```

## Task 8: Add A Collision-Safe Idempotent Installer

**Files:**
- Create: `codex-skills/tests/test_install.py`
- Create: `codex-skills/scripts/install.py`

- [ ] **Step 1: Write failing installer tests**

Test empty-home install, second-run idempotence, update of a managed link, refusal to replace a real directory, refusal to replace an unrelated symlink, explicit skip-existing behavior, dry-run behavior, and preservation of unrelated skills.

```python
def test_refuses_real_directory_collision(self):
    (self.home / "ground-truth").mkdir(parents=True)
    result = install(self.collection, self.home)
    self.assertIn("ground-truth", result.collisions)
    self.assertTrue((self.home / "ground-truth").is_dir())

def test_second_install_is_idempotent(self):
    first = install(self.collection, self.home)
    second = install(self.collection, self.home)
    self.assertEqual(58, len(first.created))
    self.assertEqual(58, len(second.unchanged))
```

- [ ] **Step 2: Run and verify installer tests fail**

Run: `python3 -m unittest tests.test_install -v`

Expected: import failure for `scripts.install`.

- [ ] **Step 3: Implement managed symlink installation**

Default source is `<repo>/codex-skills/skills`; default destination is `${CODEX_HOME:-~/.codex}/skills`. Accept `--source`, `--dest`, repeatable `--skip-existing NAME`, `--dry-run`, and `--json`. Use absolute symlink targets. Change only links whose current target is inside this collection’s `skills/` directory. A skipped existing name must already resolve to a real skill directory containing `SKILL.md`; otherwise fail. Return nonzero on unskipped collisions and make no partial changes when any collision exists.

- [ ] **Step 4: Run temporary-home integration tests twice**

Run: `python3 -m unittest tests.test_install -v`

Run: `tmp=$(mktemp -d); python3 scripts/install.py --dest "$tmp/skills"; python3 scripts/install.py --dest "$tmp/skills"; find "$tmp/skills" -type l | wc -l`

Expected: installer tests pass and the final count is `58`.

- [ ] **Step 5: Commit**

```bash
git add codex-skills/scripts/install.py codex-skills/tests/test_install.py
git commit -m "feat: install Codex skills without collisions"
```

## Task 9: Install Personally And Verify Discovery

**Files:**
- Modify: `codex-skills/VALIDATION.md`

- [ ] **Step 1: Recheck source immutability and working-tree scope**

Run: `python3 codex-skills/scripts/validate.py --source-only`

Run: `git status --short`

Expected: source hashes match; only `codex-skills/`, plan/spec docs, and the user’s pre-existing `.gitignore` modification appear.

- [ ] **Step 2: Dry-run the personal installation**

Run: `python3 codex-skills/scripts/install.py --dry-run --json`

Expected: 58 planned links or an explicit collision list; no filesystem changes.

- [ ] **Step 3: Resolve collisions conservatively**

The existing personal `last30days` skill is expected to collide. Compare its real path and content. If it remains Claude-style or otherwise cannot satisfy Codex validation, leave it untouched and record it as an explicit exclusion rather than as approved or managed. Do not replace any collision without explicit user approval.

- [ ] **Step 4: Install non-colliding skills**

Run the installer only after collision handling supports `--exclude last30days`, with that exclusion recorded separately in JSON output and without inspecting or mutating the excluded directory.

Run: `python3 codex-skills/scripts/install.py --exclude last30days --json`

Expected: 57 generated skills are linked, `last30days` is reported as the one exclusion, and all existing personal skills remain intact.

- [ ] **Step 5: Verify personal discovery and link integrity**

Run: `find /Users/brentbryson/.codex/skills -mindepth 1 -maxdepth 1 -type l -exec test -e {} \; -print | sort`

Run: `python3 codex-skills/scripts/validate.py --check --installed /Users/brentbryson/.codex/skills --exclude last30days`

Expected: all 57 managed links resolve, `last30days` is reported as excluded rather than validated, all 58 generated names are accounted for, and unrelated installed skills remain present.

- [ ] **Step 6: Update the observed validation report and commit**

Record the exact test count, generated skill count, installed link count, approved existing-skill count, excluded count, dependency-gated count, source-hash verdict, and any environment limitations.

```bash
git add codex-skills/VALIDATION.md
git commit -m "docs: record Codex skill installation verification"
```

## Task 10: Final Review And Repository Hygiene

**Files:**
- Review only: all task files and Git history

- [ ] **Step 1: Run the complete verification suite from a clean process**

Run: `cd /Users/brentbryson/claude-skills/codex-skills && python3 -m unittest discover -s tests -v && python3 scripts/build.py --check && python3 scripts/validate.py`

Expected: tests pass, build reports no diff, 58 generated skills validate, and protected-source hashes match.

- [ ] **Step 2: Verify no Claude source directory changed**

Run: `git diff 186d788 --name-only | rg -v '^(codex-skills/|docs/superpowers/)'`

Expected: only the pre-existing `.gitignore` path may appear. Inspect it but do not stage, revert, or modify it.

- [ ] **Step 3: Inspect commits and working tree**

Run: `git log --oneline 186d788..HEAD`

Run: `git status --short --branch`

Expected: task commits are present; `.gitignore` remains the user’s unstaged modification; generated outputs and reports are committed.

- [ ] **Step 4: Report completion with dependency limits**

State which skills are immediately runnable, which require external binaries/MCP/credentials, the personal installation location, the validation evidence, and that the 51 Claude sources plus `.agents-backup/` retained their baseline hashes.
