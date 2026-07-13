import io
import json
import os
import shutil
import subprocess
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from dataclasses import FrozenInstanceError
from pathlib import Path
from unittest.mock import patch

from scripts.validate import (
    CollectionReport,
    OfficialValidation,
    SkillValidation,
    SyntaxValidation,
    main,
    render_report,
    run_official_validation,
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

    def test_validation_accepts_exact_historical_claude_reference(self):
        skill = make_skill(
            self.root, body="Read historical `.claude/sessions/` as evidence.\n"
        )

        self.assertEqual((), validate_skill(skill).errors)

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
        self.assertEqual("1", runner.call_args_list[1].kwargs["env"]["UV_OFFLINE"])
        self.assertEqual("1", runner.call_args_list[2].kwargs["env"]["UV_OFFLINE"])

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


class CliTests(unittest.TestCase):
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
        self.assertEqual(["broken"], json.loads(stdout.getvalue())["errors"])
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
                self.assertEqual(0, main(["--repo", str(repo)]))
            self.assertEqual(expected, report_path.read_text(encoding="utf-8"))
            report_path.write_text("stale\n", encoding="utf-8")
            with (
                patch("scripts.validate.validate_collection", return_value=report),
                redirect_stdout(io.StringIO()),
                redirect_stderr(io.StringIO()),
            ):
                self.assertEqual(1, main(["--repo", str(repo), "--check"]))


if __name__ == "__main__":
    unittest.main()
