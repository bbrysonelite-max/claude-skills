import json
import tempfile
import unittest
from pathlib import Path

from scripts.adapt import ADAPTER_REGISTRY, validate_generated_markdown
from scripts.build import build_collection
from scripts.common import (
    Manifest,
    SkillEntry,
    hash_protected_sources,
    load_manifest,
    parse_skill_document,
    render_skill_document,
)


CODEX_SKILLS_ROOT = Path(__file__).resolve().parents[1]
REPOSITORY_ROOT = CODEX_SKILLS_ROOT.parent
MANIFEST_PATH = CODEX_SKILLS_ROOT / "manifest.yaml"
PROMOTED_ROOT = CODEX_SKILLS_ROOT / "promoted"

PROMOTED_PROVENANCE = {
    "assumptions-audit": ".agents-backup/gsd-assumptions-analyzer.md",
    "codebase-pattern-mapping": ".agents-backup/gsd-pattern-mapper.md",
    "documentation-claim-verification": ".agents-backup/gsd-doc-verifier.md",
    "integration-flow-audit": ".agents-backup/gsd-integration-checker.md",
    "requirements-coverage-audit": ".agents-backup/gsd-nyquist-auditor.md",
    "threat-mitigation-audit": ".agents-backup/gsd-security-auditor.md",
    "ai-evaluation-audit": ".agents-backup/gsd-eval-auditor.md",
}
LEGACY_PROMOTED_PROVENANCE = {
    name: f"codex-skills/archived-sources/{name}/SKILL.md"
    for name in (
        "gitnexus-cli",
        "gitnexus-debugging",
        "gitnexus-exploring",
        "gitnexus-guide",
        "gitnexus-impact-analysis",
        "gitnexus-pr-review",
        "gitnexus-refactoring",
    )
}

CONTENT_MARKERS = {
    "assumptions-audit": (
        "Confident",
        "Likely",
        "Unclear",
        "consequence if wrong",
        "external research",
        "Do not implement",
    ),
    "codebase-pattern-mapping": (
        "closest analog",
        "conventions",
        "integration points",
        "deliberate deviations",
        "risks",
        "read-only",
    ),
    "documentation-claim-verification": (
        "checkable claims",
        "exact content",
        "PASS",
        "FAIL",
        "UNVERIFIABLE",
        "BLOCKER",
        "WARNING",
    ),
    "integration-flow-audit": (
        "end-to-end",
        "boundary contracts",
        "data propagation",
        "error",
        "auth",
        "state",
        "executable evidence",
        "prioritized",
    ),
    "requirements-coverage-audit": (
        "requirement-to-test matrix",
        "executable test",
        "COVERED",
        "PARTIAL",
        "MISSING",
        "existence",
        "behavior",
    ),
    "threat-mitigation-audit": (
        "declared threat",
        "disposition",
        "mitigation",
        "absent until evidence",
        "OPEN",
        "VERIFIED",
        "ACCEPTED",
        "TRANSFERRED",
        "not a generic vulnerability scan",
    ),
    "ai-evaluation-audit": (
        "eval dimensions",
        "guardrails",
        "infrastructure",
        "COVERED",
        "PARTIAL",
        "MISSING",
        "weighted",
        "deploy verdict",
        "Do not soften",
    ),
}

PROHIBITED_COUPLING = (
    "GSD",
    "/gsd",
    ".planning/",
    ".claude/",
    "orchestrator",
    "slash command",
    "subagent",
    "AskUserQuestion",
    "TodoWrite",
    "WebSearch",
    "WebFetch",
)


def promoted_entry(name, provenance=None):
    return SkillEntry(
        source=None,
        promoted_from=provenance or PROMOTED_PROVENANCE[name],
        output=name,
        conversion="adapted",
        dependencies=(),
        notes="Promoted for direct Codex use.",
    )


def parse_interface(path):
    lines = path.read_text(encoding="utf-8").splitlines()
    values = {}
    for line in lines[1:]:
        key, raw = line.strip().split(": ", 1)
        values[key] = json.loads(raw)
    return values


class PromotedSkillContentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = load_manifest(MANIFEST_PATH, repo_root=REPOSITORY_ROOT)

    def test_exactly_fourteen_known_promoted_inputs_exist(self):
        actual = (
            {path.name for path in PROMOTED_ROOT.iterdir() if path.is_dir()}
            if PROMOTED_ROOT.is_dir()
            else set()
        )
        expected = set(PROMOTED_PROVENANCE) | set(LEGACY_PROMOTED_PROVENANCE)
        self.assertEqual(expected, actual)
        self.assertEqual(
            expected, {entry.output for entry in self.manifest.promoted}
        )

    def test_frontmatter_descriptions_runtime_and_direct_mode_are_standalone(self):
        for name in PROMOTED_PROVENANCE:
            with self.subTest(name=name):
                path = PROMOTED_ROOT / name / "SKILL.md"
                text = path.read_text(encoding="utf-8")
                document = parse_skill_document(text)
                frontmatter = text.split("---", 2)[1]
                keys = [
                    line.split(":", 1)[0]
                    for line in frontmatter.splitlines()
                    if line.strip()
                ]
                self.assertEqual(["name", "description"], keys)
                self.assertEqual(name, document.name)
                self.assertTrue(document.description.startswith("Use when "))
                self.assertNotRegex(
                    document.description,
                    r"\b(?:Run|Read|Inspect|Audit|Map|Verify|Return|Write|Generate)\b",
                )
                self.assertLess(len(document.body.splitlines()), 200)
                self.assertEqual(1, document.body.count("## Codex Runtime"))
                self.assertIn("main Codex agent", document.body)
                self.assertIn(
                    "Never print, log, or expose secret values.", document.body
                )
                self.assertIn("No special credentials", document.body)
                self.assertIn("## Inputs and Preflight", document.body)
                self.assertIn("## Workflow", document.body)
                self.assertIn("## Evidence Rules", document.body)
                self.assertIn("## Stop and Error Conditions", document.body)
                self.assertIn("## Output Contract", document.body)

    def test_each_promoted_skill_preserves_its_provenance_contract(self):
        for name, markers in CONTENT_MARKERS.items():
            text = (PROMOTED_ROOT / name / "SKILL.md").read_text(encoding="utf-8")
            for marker in markers:
                with self.subTest(name=name, marker=marker):
                    self.assertIn(marker.casefold(), text.casefold())

    def test_evidence_rules_distinguish_fact_inference_and_unverifiable(self):
        for name in PROMOTED_PROVENANCE:
            text = (PROMOTED_ROOT / name / "SKILL.md").read_text(encoding="utf-8")
            with self.subTest(name=name):
                self.assertIn("Observed fact", text)
                self.assertIn("Inference", text)
                self.assertIn("Unverifiable", text)
                self.assertRegex(text, r"path(?::line| and line|, line)")

    def test_inputs_have_no_archived_runtime_coupling_or_prohibited_markdown(self):
        for name in PROMOTED_PROVENANCE:
            text = (PROMOTED_ROOT / name / "SKILL.md").read_text(encoding="utf-8")
            validate_generated_markdown(name, "SKILL.md", text)
            for phrase in PROHIBITED_COUPLING:
                with self.subTest(name=name, phrase=phrase):
                    self.assertNotIn(phrase.casefold(), text.casefold())
            self.assertNotIn(name, ADAPTER_REGISTRY)

    def test_initialized_ui_metadata_is_complete_and_has_no_template_residue(self):
        for name in PROMOTED_PROVENANCE:
            with self.subTest(name=name):
                directory = PROMOTED_ROOT / name
                interface = parse_interface(directory / "agents/openai.yaml")
                self.assertEqual(
                    {"display_name", "short_description", "default_prompt"},
                    set(interface),
                )
                self.assertGreaterEqual(len(interface["short_description"]), 25)
                self.assertLessEqual(len(interface["short_description"]), 64)
                self.assertIn(f"${name}", interface["default_prompt"])
                for path in directory.rglob("*"):
                    if path.is_file():
                        text = path.read_text(encoding="utf-8")
                        self.assertNotIn("[TODO", text)
                        self.assertNotIn("placeholder", text.casefold())

    def test_mutation_limits_match_each_audit(self):
        read_only = {
            "codebase-pattern-mapping",
            "integration-flow-audit",
            "threat-mitigation-audit",
            "ai-evaluation-audit",
        }
        for name in read_only:
            text = (PROMOTED_ROOT / name / "SKILL.md").read_text(encoding="utf-8")
            with self.subTest(name=name):
                self.assertIn("Do not change code", text)
        doc_text = (PROMOTED_ROOT / "documentation-claim-verification" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("unless the user explicitly requests a report file", doc_text)
        coverage_text = (PROMOTED_ROOT / "requirements-coverage-audit" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("unless the user explicitly requests tests", coverage_text)


class PromotedBuildTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.repo = Path(self.temporary.name) / "repo"
        self.repo.mkdir()
        (self.repo / ".agents-backup").mkdir()
        (self.repo / "codex-skills" / "promoted").mkdir(parents=True)
        self.output = Path(self.temporary.name) / "output"

    def make_promoted(self, name="assumptions-audit", *, body=None, provenance=None):
        provenance = provenance or PROMOTED_PROVENANCE[name]
        provenance_path = self.repo / provenance
        provenance_path.parent.mkdir(parents=True, exist_ok=True)
        provenance_path.write_text("protected archived source\n", encoding="utf-8")
        directory = self.repo / "codex-skills" / "promoted" / name
        directory.mkdir(parents=True)
        text = body or (
            f"---\nname: {name}\n"
            "description: Use when a proposal needs an evidence-backed assumptions audit.\n"
            "---\n\n# Audit\n\n## Codex Runtime\n\n"
            "Operate directly in the main Codex agent. Never print, log, or expose secret values.\n"
        )
        (directory / "SKILL.md").write_text(text, encoding="utf-8")
        return directory

    def collection(self, name="assumptions-audit", *, provenance=None):
        return Manifest(
            sources=(), promoted=(promoted_entry(name, provenance=provenance),)
        )

    def test_builds_promoted_input_without_source_adapter_and_generates_ui_metadata(self):
        source = self.make_promoted()
        before = hash_protected_sources(self.repo)

        result = build_collection(self.repo, self.collection(), self.output)

        self.assertEqual(("assumptions-audit",), result.built_names)
        expected = render_skill_document(
            parse_skill_document((source / "SKILL.md").read_text(encoding="utf-8"))
        ).encode()
        self.assertEqual(expected, (self.output / "assumptions-audit/SKILL.md").read_bytes())
        interface = parse_interface(
            self.output / "assumptions-audit/agents/openai.yaml"
        )
        self.assertEqual("Assumptions Audit", interface["display_name"])
        self.assertIn("$assumptions-audit", interface["default_prompt"])
        self.assertEqual(before, hash_protected_sources(self.repo))

    def test_rejects_missing_promoted_input(self):
        provenance = self.repo / PROMOTED_PROVENANCE["assumptions-audit"]
        provenance.parent.mkdir(parents=True, exist_ok=True)
        provenance.write_text("protected archived source\n", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "promoted input.*does not exist"):
            build_collection(self.repo, self.collection(), self.output)

    def test_rejects_malformed_promoted_input(self):
        self.make_promoted(body="not frontmatter\n")
        with self.assertRaisesRegex(ValueError, "promoted.*malformed"):
            build_collection(self.repo, self.collection(), self.output)

    def test_rejects_extra_promoted_frontmatter_fields(self):
        self.make_promoted(
            body=(
                "---\nname: assumptions-audit\n"
                "description: Use when assumptions need review.\n"
                "metadata: forbidden\n---\n\n## Codex Runtime\n"
            )
        )
        with self.assertRaisesRegex(ValueError, "only name and description"):
            build_collection(self.repo, self.collection(), self.output)

    def test_rejects_missing_promoted_runtime_section(self):
        self.make_promoted(
            body=(
                "---\nname: assumptions-audit\n"
                "description: Use when assumptions need review.\n"
                "---\n\n# Audit\n"
            )
        )
        with self.assertRaisesRegex(ValueError, "Codex Runtime"):
            build_collection(self.repo, self.collection(), self.output)

    def test_rejects_unsafe_promoted_runtime_contracts(self):
        cases = {
            "missing-main-agent": (
                "Never print, log, or expose secret values.\n",
                "main Codex agent",
            ),
            "missing-secret-rule": (
                "Operate directly in the main Codex agent.\n",
                "secret-safety",
            ),
            "fixed-planning-path": (
                "Operate directly in the main Codex agent. "
                "Never print, log, or expose secret values. Read .planning/ first.\n",
                "archived runtime coupling",
            ),
            "mandatory-delegation": (
                "Operate directly in the main Codex agent. "
                "Never print, log, or expose secret values. Must use a subagent.\n",
                "unsupported delegation",
            ),
        }
        for label, (runtime, error) in cases.items():
            with self.subTest(label=label):
                with tempfile.TemporaryDirectory() as temporary:
                    original_repo, original_output = self.repo, self.output
                    try:
                        self.repo = Path(temporary) / "repo"
                        self.repo.mkdir()
                        (self.repo / ".agents-backup").mkdir()
                        (self.repo / "codex-skills/promoted").mkdir(parents=True)
                        self.output = Path(temporary) / "output"
                        self.make_promoted(
                            body=(
                                "---\nname: assumptions-audit\n"
                                "description: Use when assumptions need review.\n"
                                "---\n\n# Audit\n\n## Codex Runtime\n\n"
                                + runtime
                            )
                        )
                        with self.assertRaisesRegex(ValueError, error):
                            build_collection(self.repo, self.collection(), self.output)
                    finally:
                        self.repo, self.output = original_repo, original_output

    def test_rejects_promoted_dependency_contract(self):
        self.make_promoted()
        entry = promoted_entry("assumptions-audit")
        entry = SkillEntry(
            source=entry.source,
            promoted_from=entry.promoted_from,
            output=entry.output,
            conversion="dependency-required",
            dependencies=("special service",),
            notes=entry.notes,
        )
        with self.assertRaisesRegex(ValueError, "no dependency contract"):
            build_collection(
                self.repo,
                Manifest(sources=(), promoted=(entry,)),
                self.output,
            )

    def test_rejects_name_or_description_contract_mismatch(self):
        cases = {
            "wrong-name": (
                "---\nname: other-name\n"
                "description: Use when assumptions need review.\n---\n"
            ),
            "wrong-description": (
                "---\nname: assumptions-audit\n"
                "description: Audits assumptions.\n---\n"
            ),
        }
        for label, body in cases.items():
            with self.subTest(label=label):
                with tempfile.TemporaryDirectory() as temporary:
                    original_repo, original_output = self.repo, self.output
                    try:
                        self.repo = Path(temporary) / "repo"
                        self.repo.mkdir()
                        (self.repo / ".agents-backup").mkdir()
                        (self.repo / "codex-skills/promoted").mkdir(parents=True)
                        self.output = Path(temporary) / "output"
                        self.make_promoted(body=body)
                        with self.assertRaisesRegex(
                            ValueError, "name.*does not match|description.*Use when"
                        ):
                            build_collection(self.repo, self.collection(), self.output)
                    finally:
                        self.repo, self.output = original_repo, original_output

    def test_rejects_unknown_promoted_directory(self):
        self.make_promoted()
        unknown = self.repo / "codex-skills/promoted/unknown-audit"
        unknown.mkdir()
        (unknown / "SKILL.md").write_text("unknown\n", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "unknown promoted input.*unknown-audit"):
            build_collection(self.repo, self.collection(), self.output)

    def test_rejects_promoted_provenance_mismatch(self):
        wrong = ".agents-backup/other.md"
        self.make_promoted(provenance=wrong)
        with self.assertRaisesRegex(ValueError, "promoted provenance mismatch"):
            build_collection(
                self.repo,
                self.collection(provenance=wrong),
                self.output,
            )

    def test_rejects_prohibited_markdown_in_skill_or_resource(self):
        cases = {
            "SKILL.md": "Run the Glob tool over the repository.\n",
            "references/notes.md": "Run the Glob tool over the repository.\n",
        }
        for relative, unsafe in cases.items():
            with self.subTest(relative=relative):
                with tempfile.TemporaryDirectory() as temporary:
                    original_repo, original_output = self.repo, self.output
                    try:
                        self.repo = Path(temporary) / "repo"
                        self.repo.mkdir()
                        (self.repo / ".agents-backup").mkdir()
                        (self.repo / "codex-skills/promoted").mkdir(parents=True)
                        self.output = Path(temporary) / "output"
                        directory = self.make_promoted()
                        target = directory / relative
                        target.parent.mkdir(parents=True, exist_ok=True)
                        if relative == "SKILL.md":
                            target.write_text(
                                target.read_text(encoding="utf-8") + unsafe,
                                encoding="utf-8",
                            )
                        else:
                            target.write_text(unsafe, encoding="utf-8")
                        with self.assertRaisesRegex(ValueError, "prohibited Markdown"):
                            build_collection(self.repo, self.collection(), self.output)
                    finally:
                        self.repo, self.output = original_repo, original_output

    def test_preserves_resources_and_rebuilds_deterministically(self):
        source = self.make_promoted()
        script = source / "scripts/check.sh"
        script.parent.mkdir()
        script.write_text("#!/bin/sh\nprintf 'ok\\n'\n", encoding="utf-8")
        script.chmod(0o755)

        first = build_collection(self.repo, self.collection(), self.output)
        first_snapshot = {
            path.relative_to(self.output).as_posix(): (
                path.read_bytes(), path.stat().st_mode & 0o777
            )
            for path in self.output.rglob("*")
            if path.is_file()
        }
        second = build_collection(self.repo, self.collection(), self.output)
        second_snapshot = {
            path.relative_to(self.output).as_posix(): (
                path.read_bytes(), path.stat().st_mode & 0o777
            )
            for path in self.output.rglob("*")
            if path.is_file()
        }

        self.assertEqual(first, second)
        self.assertEqual(first_snapshot, second_snapshot)
        self.assertEqual(0o755, (self.output / "assumptions-audit/scripts/check.sh").stat().st_mode & 0o777)

    def test_real_default_build_has_manifest_output_parity(self):
        manifest = load_manifest(MANIFEST_PATH, repo_root=REPOSITORY_ROOT)
        before = hash_protected_sources(REPOSITORY_ROOT)
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "skills"
            first = build_collection(REPOSITORY_ROOT, manifest, output)
            first_bytes = {
                path.relative_to(output).as_posix(): path.read_bytes()
                for path in output.rglob("*")
                if path.is_file()
            }
            second = build_collection(REPOSITORY_ROOT, manifest, output)
            second_bytes = {
                path.relative_to(output).as_posix(): path.read_bytes()
                for path in output.rglob("*")
                if path.is_file()
            }

            expected_names = {entry.output for entry in manifest.entries}
            self.assertEqual(59, first.count)
            self.assertEqual(expected_names, set(first.built_names))
            self.assertEqual(expected_names, {p.name for p in output.iterdir() if p.is_dir()})
            self.assertEqual(first, second)
            self.assertEqual(first_bytes, second_bytes)
            self.assertEqual(
                53,
                sum(
                    (output / name / "SKILL.md")
                    .read_text(encoding="utf-8")
                    .count("## Codex Runtime")
                    for name in expected_names
                ),
            )
            for name in PROMOTED_PROVENANCE:
                expected = render_skill_document(
                    parse_skill_document(
                        (PROMOTED_ROOT / name / "SKILL.md").read_text(encoding="utf-8")
                    )
                ).encode()
                self.assertEqual(expected, (output / name / "SKILL.md").read_bytes())
                self.assertTrue((output / name / "agents/openai.yaml").is_file())
        self.assertEqual(before, hash_protected_sources(REPOSITORY_ROOT))


if __name__ == "__main__":
    unittest.main()
