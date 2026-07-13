import io
import json
import os
import shutil
import subprocess
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from dataclasses import FrozenInstanceError, replace
from pathlib import Path
from unittest.mock import patch

from scripts.common import SkillEntry
from scripts.validate import (
    CollectionReport,
    InjectedDefectValidation,
    OfficialValidation,
    RegressionValidation,
    SkillValidation,
    SyntaxValidation,
    _dependency_status,
    _structural_fingerprint,
    main,
    render_report,
    run_injected_defect_validation,
    run_official_validation,
    run_regression_validation,
    validate_collection,
    validate_skill,
)


CODEX_SKILLS_ROOT = Path(__file__).resolve().parents[1]
REPOSITORY_ROOT = CODEX_SKILLS_ROOT.parent


def metadata(name: str = "sample") -> str:
    return (
        "interface:\n"
        f'  display_name: "{name.replace("-", " ").title()}"\n'
        '  short_description: "A short useful sample description."\n'
        f'  default_prompt: "Use ${name} to follow the documented workflow."\n'
    )


def make_skill(
    root: Path,
    name: str = "sample",
    body: str = "# Sample\n",
    description: str = "Use when a sample validation fixture is needed.",
) -> Path:
    skill = root / name
    (skill / "agents").mkdir(parents=True)
    (skill / "SKILL.md").write_text(
        f'---\nname: "{name}"\ndescription: "{description}"\n---\n\n{body}',
        encoding="utf-8",
    )
    (skill / "agents" / "openai.yaml").write_text(
        metadata(name), encoding="utf-8"
    )
    return skill


def source_entry(
    name: str,
    conversion: str = "native",
    dependencies: tuple[str, ...] = (),
) -> dict:
    return {
        "source": name,
        "promoted_from": None,
        "output": name,
        "conversion": conversion,
        "dependencies": list(dependencies),
        "notes": "Validation fixture.",
    }


class SkillValidationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)

    def tearDown(self):
        self.temporary.cleanup()

    def test_validation_records_are_structured_and_immutable(self):
        syntax = SyntaxValidation("python", "python3", ("sample.py",), ())
        official = OfficialValidation("sample", True, "validated")
        result = SkillValidation(self.root / "sample", "sample", (), (), 1, (syntax,))
        report = CollectionReport(
            repo_root=self.root,
            generated_on="2026-07-13",
            skill_results=(result,),
            errors=(),
            warnings=(),
            class_counts=(("native", 1),),
            source_hash_count=2,
            source_hashes_match=True,
            markdown_count=1,
            resource_count=2,
            runtime_count=0,
            native_runtime_absent_count=1,
            dependency_preflight_count=0,
            dependency_secret_count=0,
            syntax_results=(syntax,),
            official_results=(official,),
            dependency_statuses=(),
            installed_count=None,
            source_only=False,
        )

        with self.assertRaises(FrozenInstanceError):
            result.name = "changed"
        with self.assertRaises(FrozenInstanceError):
            report.errors = ("changed",)
        self.assertIsInstance(result.errors, tuple)
        self.assertEqual(1, report.skill_count)
        self.assertTrue(report.ok)

    def test_validate_skill_accepts_minimal_valid_skill(self):
        skill = make_skill(self.root)

        result = validate_skill(skill)

        self.assertEqual((), result.errors)
        self.assertEqual(1, result.markdown_count)

    def test_validation_rejects_claude_only_operational_instruction(self):
        skill = make_skill(self.root, body="Use the AskUserQuestion tool now.\n")

        result = validate_skill(skill)

        self.assertTrue(any("AskUserQuestion" in error for error in result.errors))

    def test_validation_accepts_exact_path_scoped_historical_claude_reference(self):
        skill = make_skill(
            self.root,
            name="closing-ritual",
            body=(
                "Treat historical `.claude/sessions/` files as read-only evidence; "
                "never write new snapshots there.\n"
            ),
        )

        self.assertEqual((), validate_skill(skill).errors)

        same_literal_wrong_path = make_skill(
            self.root,
            name="sample",
            body=(
                "Treat historical `.claude/sessions/` files as read-only evidence; "
                "never write new snapshots there.\n"
            ),
        )
        self.assertTrue(
            any(
                "Claude runtime/client/environment" in error
                for error in validate_skill(same_literal_wrong_path).errors
            )
        )

    def test_validation_rejects_claude_code_session_variable_injection(self):
        skill = make_skill(
            self.root,
            body=(
                "Run this workflow only in Claude Code and write to "
                "${CLAUDE_SESSION_ID}.\n"
            ),
        )

        result = validate_skill(skill)

        self.assertTrue(
            any("Claude runtime/client/environment" in error for error in result.errors)
        )

    def test_validation_rejects_active_claude_path(self):
        skill = make_skill(
            self.root, body="Write the result to `~/.claude/skills/sample/output.md`.\n"
        )

        result = validate_skill(skill)

        self.assertTrue(any("active Claude path" in error for error in result.errors))

    def test_validation_rejects_wrong_frontmatter_and_folder_name(self):
        skill = make_skill(self.root)
        (skill / "SKILL.md").write_text(
            "---\nname: wrong\ndescription: useful\nextra: forbidden\n---\nbody\n",
            encoding="utf-8",
        )

        result = validate_skill(skill)

        self.assertTrue(any("frontmatter" in error for error in result.errors))
        self.assertTrue(any("folder" in error for error in result.errors))

    def test_validation_rejects_angle_brackets_in_description(self):
        skill = make_skill(
            self.root,
            description="Use when choosing an <industry> placeholder.",
        )

        result = validate_skill(skill)

        self.assertTrue(any("angle brackets" in error for error in result.errors))

    def test_validation_rejects_wrong_openai_metadata_and_long_short_description(self):
        skill = make_skill(self.root)
        (skill / "agents" / "openai.yaml").write_text(
            "interface:\n"
            '  display_name: "Sample"\n'
            f'  short_description: "{"x" * 101}"\n'
            '  default_prompt: "Use the skill."\n'
            '  extra: "forbidden"\n',
            encoding="utf-8",
        )

        result = validate_skill(skill)

        self.assertTrue(any("interface fields" in error for error in result.errors))
        self.assertTrue(any("100" in error for error in result.errors))
        self.assertTrue(any("$sample" in error for error in result.errors))

    def test_validation_reports_broken_markdown_link_with_path_and_line(self):
        skill = make_skill(self.root, body="See [missing](references/missing.md).\n")

        result = validate_skill(skill)

        self.assertTrue(
            any(
                "SKILL.md:" in error and "references/missing.md" in error
                for error in result.errors
            )
        )

    def test_validation_rejects_missing_inline_resource_without_family_directory(self):
        skill = make_skill(self.root, body="Run `scripts/missing.py` now.\n")

        result = validate_skill(skill)

        self.assertTrue(
            any("scripts/missing.py" in error for error in result.errors)
        )

    def test_validation_rejects_missing_dot_slash_inline_resource(self):
        skill = make_skill(self.root, body="Run `./scripts/missing.py` now.\n")

        result = validate_skill(skill)

        self.assertTrue(
            any("./scripts/missing.py" in error for error in result.errors)
        )

    def test_validation_rejects_broken_reference_style_link(self):
        skill = make_skill(
            self.root,
            body="Read the [guide][g].\n\n[g]: references/missing.md\n",
        )

        result = validate_skill(skill)

        self.assertTrue(
            any("references/missing.md" in error for error in result.errors)
        )

    def test_validation_rejects_broken_shortcut_reference_style_link(self):
        skill = make_skill(
            self.root,
            body="Read the [guide].\n\n[guide]: docs/missing.md\n",
        )

        result = validate_skill(skill)

        self.assertTrue(any("docs/missing.md" in error for error in result.errors))

    def test_validation_accepts_balanced_parentheses_in_link_destination(self):
        skill = make_skill(
            self.root,
            body="Read [the guide](references/a(b).md).\n",
        )
        references = skill / "references"
        references.mkdir()
        (references / "a(b).md").write_text("# Guide\n", encoding="utf-8")

        self.assertEqual((), validate_skill(skill).errors)

    def test_validation_accepts_escaped_titled_reference_and_anchor_links(self):
        skill = make_skill(
            self.root,
            body=(
                "Read [escaped](references/a\\(b\\).md \"Guide\"), "
                "[angle](<references/a(b).md> 'Guide'), and [reference][g]. "
                "Jump to [section](#section).\n\n"
                "[g]: references/a(b).md \"Reference guide\"\n"
            ),
        )
        references = skill / "references"
        references.mkdir()
        (references / "a(b).md").write_text("# Guide\n", encoding="utf-8")

        self.assertEqual((), validate_skill(skill).errors)

    def test_validation_allows_external_anchor_and_templated_links(self):
        skill = make_skill(
            self.root,
            body=(
                "[web](https://example.com) [mail](mailto:test@example.com) "
                "[anchor](#section) [template]({OUTPUT_PATH})\n"
            ),
        )

        self.assertEqual((), validate_skill(skill).errors)

    def test_validation_rejects_escaping_symlink(self):
        skill = make_skill(self.root, body="See [outside](escape.md).\n")
        outside = self.root / "outside.md"
        outside.write_text("outside\n", encoding="utf-8")
        (skill / "escape.md").symlink_to(outside)

        result = validate_skill(skill)

        self.assertTrue(any("symlink escapes" in error for error in result.errors))

    def test_validation_accumulates_bad_python_shell_and_javascript_syntax(self):
        skill = make_skill(self.root)
        scripts = skill / "scripts"
        scripts.mkdir()
        (scripts / "bad.py").write_text("def broken(:\n", encoding="utf-8")
        (scripts / "bad.sh").write_text("if then\n", encoding="utf-8")
        (scripts / "bad.js").write_text("function {\n", encoding="utf-8")

        result = validate_skill(skill)

        self.assertTrue(any("bad.py" in error for error in result.errors))
        self.assertTrue(any("bad.sh" in error for error in result.errors))
        self.assertTrue(any("bad.js" in error for error in result.errors))
        self.assertGreaterEqual(len(result.errors), 3)

    def test_validation_rejects_crlf_and_unresolved_markers(self):
        skill = make_skill(self.root)
        with (skill / "SKILL.md").open("w", encoding="utf-8", newline="") as output:
            output.write(
                '---\r\nname: "sample"\r\ndescription: "Useful sample."\r\n'
                "---\r\n\r\nTODO: replace {{SKILL_NAME}}\r\n"
            )

        result = validate_skill(skill)

        self.assertTrue(any("CRLF" in error for error in result.errors))
        self.assertTrue(any("placeholder" in error for error in result.errors))


class CollectionValidationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.repo = Path(self.temporary.name)
        (self.repo / "codex-skills" / "skills").mkdir(parents=True)
        (self.repo / ".agents-backup").mkdir()

    def tearDown(self):
        self.temporary.cleanup()

    def write_manifest(self, sources=(), promoted=()):
        path = self.repo / "codex-skills" / "manifest.yaml"
        path.write_text(
            json.dumps({"sources": list(sources), "promoted": list(promoted)}, indent=2)
            + "\n",
            encoding="utf-8",
        )

    def make_source_and_output(
        self,
        name="sample",
        conversion="native",
        dependencies=(),
        body="# Sample\n",
    ):
        make_skill(self.repo, name, body=body)
        output = make_skill(self.repo / "codex-skills" / "skills", name, body=body)
        self.write_manifest((source_entry(name, conversion, dependencies),))
        from scripts.common import hash_protected_sources

        (self.repo / "codex-skills" / "source-hashes.json").write_text(
            json.dumps(hash_protected_sources(self.repo), indent=2) + "\n",
            encoding="utf-8",
        )
        return output

    @staticmethod
    def passed_official(skill_paths):
        return tuple(
            OfficialValidation(path.name, True, "validated") for path in skill_paths
        )

    def validate_fixture(self, **kwargs):
        with patch(
            "scripts.validate.run_official_validation",
            side_effect=self.passed_official,
        ):
            return validate_collection(self.repo, **kwargs)

    def test_collection_reports_extra_and_missing_outputs_together(self):
        self.make_source_and_output("expected")
        shutil.rmtree(self.repo / "codex-skills" / "skills" / "expected")
        make_skill(self.repo / "codex-skills" / "skills", "extra")

        report = self.validate_fixture()

        self.assertTrue(any("missing output" in error for error in report.errors))
        self.assertTrue(any("extra output" in error for error in report.errors))

    def test_collection_reports_source_hash_drift(self):
        self.make_source_and_output()
        (self.repo / "sample" / "SKILL.md").write_text("drifted\n", encoding="utf-8")

        report = self.validate_fixture()

        self.assertFalse(report.source_hashes_match)
        self.assertTrue(any("source hash drift" in error for error in report.errors))

    def test_collection_requires_runtime_dependency_preflight_and_secret_clause(self):
        output = self.make_source_and_output(
            conversion="dependency-required", dependencies=("sample CLI",)
        )
        (output / "SKILL.md").write_text(
            '---\nname: "sample"\ndescription: "Useful sample."\n---\n\n'
            "# Sample\n\n## Codex Runtime\n\nMandatory dependencies:\n"
            "- `wrong dependency`\n",
            encoding="utf-8",
        )

        report = self.validate_fixture()

        self.assertTrue(any("dependency list" in error for error in report.errors))
        self.assertTrue(any("preflight" in error.lower() for error in report.errors))
        self.assertTrue(any("secret" in error.lower() for error in report.errors))

    def test_collection_rejects_promoted_gsd_planning_coupling(self):
        provenance = self.repo / ".agents-backup" / "gsd-assumptions-analyzer.md"
        provenance.write_text("archived\n", encoding="utf-8")
        promoted_input = make_skill(
            self.repo / "codex-skills" / "promoted",
            "assumptions-audit",
            body="# Audit\n\n## Codex Runtime\n",
        )
        output = make_skill(
            self.repo / "codex-skills" / "skills",
            "assumptions-audit",
            body="# Audit\n\nRead `.planning/STATE.md` through the GSD orchestrator.\n"
            "\n## Codex Runtime\n",
        )
        promoted = {
            "source": None,
            "promoted_from": ".agents-backup/gsd-assumptions-analyzer.md",
            "output": "assumptions-audit",
            "conversion": "adapted",
            "dependencies": [],
            "notes": "Promoted fixture.",
        }
        self.write_manifest((), (promoted,))
        from scripts.common import hash_protected_sources

        (self.repo / "codex-skills" / "source-hashes.json").write_text(
            json.dumps(hash_protected_sources(self.repo), indent=2) + "\n",
            encoding="utf-8",
        )

        report = self.validate_fixture()

        self.assertTrue(any("promoted runtime coupling" in error for error in report.errors))
        self.assertTrue(promoted_input.is_dir() and output.is_dir())

    def test_collection_aggregates_official_validator_failure(self):
        self.make_source_and_output()

        with patch(
            "scripts.validate.run_official_validation",
            return_value=(OfficialValidation("sample", False, "invalid frontmatter"),),
        ):
            report = validate_collection(self.repo)

        self.assertTrue(any("official validator" in error for error in report.errors))
        self.assertEqual(1, report.official_failures)

    def test_official_validation_short_circuits_shared_uv_resolution_failure(self):
        first = self.repo / "alpha"
        second = self.repo / "beta"
        first.mkdir()
        second.mkdir()
        failure = subprocess.CompletedProcess(
            args=[],
            returncode=2,
            stdout="",
            stderr=(
                "Request failed after 3 retries in 10.2s\n"
                "Failed to fetch: https://pypi.org/simple/pyyaml/\n"
                "Caused by: dns error"
            ),
        )

        with (
            patch("scripts.validate.shutil.which", return_value="/usr/bin/uv"),
            patch("scripts.validate.subprocess.run", return_value=failure) as runner,
        ):
            results = run_official_validation((first, second))

        self.assertEqual(2, runner.call_count)
        self.assertEqual(("alpha", "beta"), tuple(result.name for result in results))
        self.assertTrue(all(not result.passed for result in results))
        self.assertTrue(all("dns error" in result.output for result in results))
        self.assertTrue(all("10.2s" not in result.output for result in results))

    def test_official_validation_uses_cached_offline_uv_after_network_failure(self):
        first = self.repo / "alpha"
        second = self.repo / "beta"
        first.mkdir()
        second.mkdir()
        failure = subprocess.CompletedProcess(
            args=[],
            returncode=2,
            stdout="",
            stderr=(
                "Failed to fetch: https://pypi.org/simple/pyyaml/\n"
                "Caused by: dns error"
            ),
        )
        success = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="Skill is valid!\n", stderr=""
        )

        with (
            patch("scripts.validate.shutil.which", return_value="/usr/bin/uv"),
            patch(
                "scripts.validate.subprocess.run",
                side_effect=(failure, success, success),
            ) as runner,
        ):
            results = run_official_validation((first, second))

        self.assertEqual(3, runner.call_count)
        self.assertTrue(all(result.passed for result in results))
        self.assertEqual("offline-cached-fallback", results[0].execution_mode)
        self.assertEqual("offline-cached", results[1].execution_mode)
        self.assertIn("PyYAML", results[0].initial_diagnostic)
        self.assertIn("DNS", results[0].initial_diagnostic)
        self.assertNotIn("pypi.org", results[0].initial_diagnostic)
        self.assertEqual("1", runner.call_args_list[1].kwargs["env"]["UV_OFFLINE"])
        self.assertEqual("1", runner.call_args_list[2].kwargs["env"]["UV_OFFLINE"])

    def test_regression_validation_records_observed_counts_without_ambient_bypass(self):
        version = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="Python 3.14.5\n", stderr=""
        )
        suite = subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout="",
            stderr="Ran 193 tests in 1.234s\n\nOK\n",
        )

        with (
            patch(
                "scripts.validate._python_executables",
                return_value=("/usr/local/bin/python3",),
            ),
            patch(
                "scripts.validate.subprocess.run", side_effect=(version, suite)
            ) as runner,
        ):
            results = run_regression_validation(self.repo)

        self.assertEqual(1, len(results))
        self.assertTrue(results[0].passed)
        self.assertEqual(193, results[0].tests_run)
        self.assertEqual("Python 3.14.5", results[0].interpreter)
        self.assertNotIn(
            "CODEX_VALIDATE_INTERNAL_TEST_MODE",
            runner.call_args_list[1].kwargs.get("env", {}),
        )

    def test_ambient_internal_mode_cannot_suppress_requested_evidence(self):
        self.make_source_and_output()
        with (
            patch.dict(os.environ, {"CODEX_VALIDATE_INTERNAL_TEST_MODE": "1"}),
            patch("scripts.validate.EXPECTED_SKILL_COUNT", 1),
            patch("scripts.validate.EXPECTED_SOURCE_COUNT", 1),
            patch("scripts.validate.EXPECTED_PROMOTED_COUNT", 0),
            patch(
                "scripts.validate.EXPECTED_CLASS_COUNTS",
                {"adapted": 0, "dependency-required": 0, "native": 1},
            ),
            patch("scripts.validate.run_regression_validation", return_value=()),
            patch("scripts.validate.run_injected_defect_validation", return_value=()),
        ):
            report = self.validate_fixture(collect_evidence=True)

        self.assertTrue(
            any(
                "regression suite evidence is missing" in error
                for error in report.errors
            )
        )
        self.assertTrue(
            any(
                "injected defect validation evidence is missing" in error
                for error in report.errors
            )
        )

    def test_structural_only_rejects_requested_evidence_as_suppressed(self):
        self.make_source_and_output()

        report = validate_collection(
            self.repo, collect_evidence=True, structural_only=True
        )

        self.assertTrue(
            any("evidence was requested but suppressed" in error for error in report.errors)
        )

    def test_injected_defect_validation_observes_required_categories(self):
        results = run_injected_defect_validation()

        categories = {result.category for result in results}
        self.assertEqual(
            {
                "Claude runtime compatibility",
                "frontmatter and metadata",
                "local resource integrity",
                "resource syntax",
            },
            categories,
        )
        self.assertTrue(all(result.passed for result in results))

    def test_source_only_ignores_missing_generated_output(self):
        self.make_source_and_output()
        shutil.rmtree(self.repo / "codex-skills" / "skills")

        report = validate_collection(self.repo, source_only=True)

        self.assertTrue(report.source_only)
        self.assertFalse(any("generated output" in error for error in report.errors))
        self.assertFalse(any("missing output" in error for error in report.errors))
        self.assertEqual((), report.official_results)

    def test_installed_validation_requires_links_to_generated_names(self):
        output = self.make_source_and_output()
        installed = self.repo / "installed"
        installed.mkdir()
        (installed / "sample").symlink_to(output, target_is_directory=True)

        report = self.validate_fixture(installed=installed)

        self.assertEqual(1, report.installed_count)
        self.assertFalse(any("installed" in error for error in report.errors))

        (installed / "sample").unlink()
        (installed / "sample").mkdir()
        report = self.validate_fixture(installed=installed)
        self.assertTrue(any("installed" in error for error in report.errors))

    def test_installed_validation_accepts_explicitly_approved_existing_skill(self):
        self.make_source_and_output("last30days")
        installed = self.repo / "installed"
        installed.mkdir()
        make_skill(installed, "last30days")

        report = self.validate_fixture(
            installed=installed, approved_existing=("last30days",)
        )

        self.assertEqual(0, report.installed_count)
        self.assertEqual(1, report.approved_existing_count)
        self.assertFalse(any("installed" in error for error in report.errors))

    def test_installed_validation_rejects_invalid_or_unapproved_existing_skill(self):
        self.make_source_and_output("last30days")
        installed = self.repo / "installed"
        installed.mkdir()
        existing = make_skill(installed, "last30days")
        (existing / "SKILL.md").write_text(
            '---\nname: "wrong-name"\ndescription: "Useful fixture."\n---\n',
            encoding="utf-8",
        )

        invalid = self.validate_fixture(
            installed=installed, approved_existing=("last30days",)
        )
        unapproved = self.validate_fixture(installed=installed)

        self.assertTrue(any("frontmatter name" in error for error in invalid.errors))
        self.assertTrue(any("must be a managed symlink" in error for error in unapproved.errors))

    def test_installed_validation_rejects_escaping_symlink_in_approved_existing(self):
        self.make_source_and_output("last30days")
        installed = self.repo / "installed"
        installed.mkdir()
        existing = make_skill(installed, "last30days")
        outside = self.repo / "outside.txt"
        outside.write_text("outside\n", encoding="utf-8")
        (existing / "escape.txt").symlink_to(outside)

        report = self.validate_fixture(
            installed=installed, approved_existing=("last30days",)
        )

        self.assertTrue(any("symlink escapes" in error for error in report.errors))

    def test_dependency_status_requires_every_mandatory_probe_to_succeed(self):
        entry = SkillEntry(
            "tiger-whitepaper",
            None,
            "tiger-whitepaper",
            "dependency-required",
            ("Node.js", "Google Chrome"),
            "Fixture.",
        )

        with (
            patch(
                "scripts.validate.shutil.which",
                side_effect=lambda command: "/usr/bin/node" if command == "node" else None,
            ),
            patch("scripts.validate.Path.is_file", return_value=False),
        ):
            status = _dependency_status(entry)

        self.assertEqual("missing", status.status)
        self.assertEqual(
            (("Node.js", "available"), ("Google Chrome", "missing")),
            tuple((probe.dependency, probe.status) for probe in status.probes),
        )

    def test_dependency_status_marks_unknown_mandatory_probe_partial(self):
        entry = SkillEntry(
            "sample",
            None,
            "sample",
            "dependency-required",
            ("Unknown bespoke runtime",),
            "Fixture.",
        )

        status = _dependency_status(entry)

        self.assertEqual("partial", status.status)
        self.assertEqual("not-probed", status.probes[0].status)

    def test_dependency_status_unknown_keeps_mixed_entry_partial(self):
        entry = SkillEntry(
            "sample",
            None,
            "sample",
            "dependency-required",
            ("Unknown bespoke runtime", "publishing credentials"),
            "Fixture.",
        )

        status = _dependency_status(entry)

        self.assertEqual("partial", status.status)
        self.assertEqual(
            ("not-probed", "credential-dependent"),
            tuple(probe.status for probe in status.probes),
        )

    def test_dependency_status_accepts_macos_chrome_application_probe(self):
        entry = SkillEntry(
            "sample",
            None,
            "sample",
            "dependency-required",
            ("Google Chrome",),
            "Fixture.",
        )

        with (
            patch("scripts.validate.shutil.which", return_value=None),
            patch(
                "scripts.validate.Path.is_file",
                autospec=True,
                side_effect=lambda path: "Google Chrome.app" in str(path),
            ),
        ):
            status = _dependency_status(entry)

        self.assertEqual("available", status.status)
        self.assertEqual("available", status.probes[0].status)

    def test_canonical_collection_has_observed_58_skill_contract(self):
        with patch(
            "scripts.validate.run_official_validation",
            side_effect=self.passed_official,
        ):
            report = validate_collection(REPOSITORY_ROOT)

        self.assertEqual(58, report.skill_count)
        self.assertEqual(
            (("adapted", 12), ("dependency-required", 40), ("native", 6)),
            report.class_counts,
        )
        self.assertEqual(52, report.runtime_count)
        self.assertEqual(6, report.native_runtime_absent_count)
        self.assertEqual(40, report.dependency_preflight_count)
        self.assertEqual(40, report.dependency_secret_count)
        self.assertEqual((), report.errors)

    def test_report_uses_observed_counts_and_lists_all_dependency_skills(self):
        with patch(
            "scripts.validate.run_official_validation",
            side_effect=self.passed_official,
        ):
            report = validate_collection(REPOSITORY_ROOT)

        text = render_report(report)

        self.assertIn("58 total", text)
        self.assertIn("6 native", text)
        self.assertIn("12 adapted", text)
        self.assertIn("40 dependency-required", text)
        self.assertIn("| `agent-reach` |", text)
        self.assertIn("| `whitelabel-radar` |", text)
        self.assertEqual(40, len(report.dependency_statuses))
        self.assertIn("No live external workflows", text)

    def test_report_lists_exact_per_dependency_probe_statuses(self):
        with patch(
            "scripts.validate.run_official_validation",
            side_effect=self.passed_official,
        ):
            report = validate_collection(REPOSITORY_ROOT)

        text = render_report(report)

        self.assertRegex(text, r"`Node\.js` \((?:available|missing)\)")
        self.assertRegex(text, r"`Google Chrome` \((?:available|missing)\)")

    def test_report_renders_observed_fallback_regressions_and_injections(self):
        report = replace(
            CollectionReport.empty(self.repo),
            official_results=(
                OfficialValidation(
                    "sample",
                    True,
                    "Skill is valid!",
                    "offline-cached-fallback",
                    "uv PyYAML dependency resolution failed because DNS lookup failed",
                ),
            ),
            regression_results=(
                RegressionValidation("Python 3.14.5", 193, True, ""),
                RegressionValidation("Python 3.11.15", 193, True, ""),
            ),
            injected_defect_results=(
                InjectedDefectValidation(
                    "Claude runtime compatibility", "session variable", True, ""
                ),
                InjectedDefectValidation(
                    "local resource integrity", "missing script", True, ""
                ),
            ),
        )

        text = render_report(report)

        self.assertIn("offline-cached-fallback", text)
        self.assertIn("DNS lookup failed", text)
        self.assertIn("Python 3.14.5", text)
        self.assertIn("193/193", text)
        self.assertIn(
            "| Claude runtime compatibility | `session variable` | detected | PASS |",
            text,
        )

    def test_report_lists_every_observed_injected_defect_once_and_totals_nine(self):
        injected = run_injected_defect_validation()
        report = replace(
            CollectionReport.empty(self.repo),
            injected_defect_results=injected,
        )

        text = render_report(report)

        self.assertEqual(9, len(injected))
        self.assertIn("**Injected defect checks:** **PASS**; 9/9 detected", text)
        for result in injected:
            with self.subTest(name=result.name):
                self.assertEqual(1, text.count(f"| `{result.name}` |"))
                self.assertIn(f"| {result.category} | `{result.name}` |", text)

    def test_report_does_not_claim_unobserved_regression_or_injection_passes(self):
        text = render_report(CollectionReport.empty(self.repo))

        self.assertIn("Regression suites: **NOT OBSERVED**", text)
        self.assertIn("Injected defect checks: **NOT OBSERVED**", text)
        self.assertNotIn("Regression suites: **PASS**", text)
        self.assertNotIn("Injected defect checks: **PASS**", text)


class CliTests(unittest.TestCase):
    def test_default_cli_explicitly_requests_observed_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            report = CollectionReport.empty(repo)
            with (
                patch("scripts.validate.validate_collection", return_value=report) as validator,
                redirect_stdout(io.StringIO()),
            ):
                self.assertEqual(1, main(["--repo", str(repo)]))
            self.assertIn(
                "**Overall:** FAIL",
                (repo / "codex-skills" / "VALIDATION.md").read_text(encoding="utf-8"),
            )

        validator.assert_called_once_with(
            repo,
            installed=None,
            approved_existing=(),
            source_only=False,
            collect_evidence=True,
            structural_only=False,
        )

    def test_ambient_internal_mode_cannot_write_pass_without_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            report = CollectionReport.empty(repo)
            with (
                patch.dict(os.environ, {"CODEX_VALIDATE_INTERNAL_TEST_MODE": "1"}),
                patch("scripts.validate.validate_collection", return_value=report),
                redirect_stdout(io.StringIO()),
            ):
                self.assertEqual(1, main(["--repo", str(repo)]))

            text = (repo / "codex-skills" / "VALIDATION.md").read_text(encoding="utf-8")
            self.assertIn("**Overall:** FAIL", text)
            self.assertIn("**NOT OBSERVED**", text)

    def test_explicit_test_child_path_skips_evidence_and_report_writes(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            report = CollectionReport.empty(repo)
            with (
                patch("scripts.validate.validate_collection", return_value=report) as validator,
                redirect_stdout(io.StringIO()),
            ):
                self.assertEqual(0, main(["--repo", str(repo), "--test-child"]))

            self.assertFalse((repo / "codex-skills" / "VALIDATION.md").exists())
            validator.assert_called_once_with(
                repo,
                installed=None,
                approved_existing=(),
                source_only=False,
                collect_evidence=False,
                structural_only=False,
            )

    def test_cli_forwards_repeatable_approved_existing_names(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            installed = repo / "installed"
            report = CollectionReport.empty(repo)
            with (
                patch("scripts.validate.validate_collection", return_value=report) as validator,
                redirect_stdout(io.StringIO()),
            ):
                self.assertEqual(
                    0,
                    main(
                        [
                            "--repo",
                            str(repo),
                            "--installed",
                            str(installed),
                            "--approved-existing",
                            "last30days",
                            "--approved-existing",
                            "existing-two",
                            "--test-child",
                        ]
                    ),
                )

        validator.assert_called_once_with(
            repo,
            installed=installed,
            approved_existing=("last30days", "existing-two"),
            source_only=False,
            collect_evidence=False,
            structural_only=False,
        )

    def test_source_only_and_check_are_rejected_as_incompatible(self):
        stderr = io.StringIO()
        with (
            patch("scripts.validate.validate_collection") as validator,
            redirect_stderr(stderr),
            self.assertRaises(SystemExit) as raised,
        ):
            main(["--source-only", "--check"])

        self.assertEqual(2, raised.exception.code)
        self.assertIn("--source-only", stderr.getvalue())
        self.assertIn("--check", stderr.getvalue())
        validator.assert_not_called()

    def test_json_cli_returns_nonzero_and_structured_output_on_errors(self):
        report = CollectionReport.empty(Path("/tmp/repo"), errors=("broken",))
        stdout = io.StringIO()
        stderr = io.StringIO()
        with (
            patch("scripts.validate.validate_collection", return_value=report),
            redirect_stdout(stdout),
            redirect_stderr(stderr),
        ):
            exit_code = main(["--repo", "/tmp/repo", "--json"])

        self.assertEqual(1, exit_code)
        self.assertEqual(
            [
                "broken",
                "requested full report regression evidence is missing",
                "requested full report injected defect evidence is missing",
            ],
            json.loads(stdout.getvalue())["errors"],
        )
        self.assertEqual("", stderr.getvalue())

    def test_default_cli_writes_text_report_and_check_detects_drift(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            report_path = repo / "codex-skills" / "VALIDATION.md"
            report = CollectionReport.empty(repo)
            expected = render_report(report)
            stdout = io.StringIO()
            with (
                patch("scripts.validate.validate_collection", return_value=report),
                redirect_stdout(stdout),
            ):
                self.assertEqual(1, main(["--repo", str(repo)]))
            self.assertNotEqual(expected, report_path.read_text(encoding="utf-8"))
            report_path.write_text("stale\n", encoding="utf-8")
            with (
                patch("scripts.validate.validate_collection", return_value=report),
                redirect_stdout(io.StringIO()),
                redirect_stderr(io.StringIO()),
            ):
                self.assertEqual(1, main(["--repo", str(repo), "--check"]))

    def test_check_ignores_volatile_observations_when_fingerprint_matches(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            report_path = repo / "codex-skills" / "VALIDATION.md"
            report_path.parent.mkdir(parents=True)
            fingerprint = _structural_fingerprint(repo)
            report_path.write_text(
                "# Old observed report\n\n"
                "- **Observed date:** 2099-01-01\n"
                f"- **Structural fingerprint:** `{fingerprint}`\n"
                "- Python 9.99 from /another/host\n"
                "- Google Chrome (available on another host)\n",
                encoding="utf-8",
            )
            report = replace(
                CollectionReport.empty(repo), structural_fingerprint=fingerprint
            )
            with (
                patch("scripts.validate.validate_collection", return_value=report) as validator,
                redirect_stdout(io.StringIO()),
                redirect_stderr(io.StringIO()),
            ):
                self.assertEqual(0, main(["--repo", str(repo), "--check"]))

        validator.assert_called_once_with(
            repo,
            installed=None,
            approved_existing=(),
            source_only=False,
            collect_evidence=False,
            structural_only=True,
        )

    def test_check_rejects_structural_mutation_after_report(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            generated = repo / "codex-skills" / "skills" / "sample"
            generated.mkdir(parents=True)
            payload = generated / "SKILL.md"
            payload.write_text("before\n", encoding="utf-8")
            old_fingerprint = _structural_fingerprint(repo)
            report_path = repo / "codex-skills" / "VALIDATION.md"
            report_path.write_text(
                f"- **Structural fingerprint:** `{old_fingerprint}`\n",
                encoding="utf-8",
            )
            payload.write_text("after\n", encoding="utf-8")
            new_fingerprint = _structural_fingerprint(repo)
            report = replace(
                CollectionReport.empty(repo), structural_fingerprint=new_fingerprint
            )

            with (
                patch("scripts.validate.validate_collection", return_value=report),
                redirect_stdout(io.StringIO()),
                redirect_stderr(io.StringIO()),
            ):
                self.assertEqual(1, main(["--repo", str(repo), "--check"]))

        self.assertNotEqual(old_fingerprint, new_fingerprint)


if __name__ == "__main__":
    unittest.main()
