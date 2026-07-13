import io
import json
import os
import shutil
import stat
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch

from scripts.adapt import ADAPTER_REGISTRY, AdapterSpec
from scripts.build import BuildResult, build_collection, main
from scripts.common import (
    Manifest,
    SkillEntry,
    hash_protected_sources,
    parse_skill_document,
    render_skill_document,
)


CODEX_SKILLS_ROOT = Path(__file__).resolve().parents[1]
REPOSITORY_ROOT = CODEX_SKILLS_ROOT.parent


def entry(name="sample", output=None):
    return SkillEntry(
        source=name,
        promoted_from=None,
        output=output or name,
        conversion="native",
        dependencies=(),
        notes="Works directly in Codex.",
    )


def manifest(*entries):
    return Manifest(sources=tuple(entries), promoted=())


def promoted_entry(output="promoted", provenance=".agents-backup/archived.md"):
    return SkillEntry(
        source=None,
        promoted_from=provenance,
        output=output,
        conversion="adapted",
        dependencies=(),
        notes="Promoted for Codex.",
    )


class FrontmatterTests(unittest.TestCase):
    def test_parses_all_supported_description_scalar_styles(self):
        cases = {
            "A plain: useful description.": (
                "A plain: useful description.",
                "A plain: useful description.",
            ),
            "'single quoted description'": (
                "single quoted description",
                "single quoted description",
            ),
            "'single''s quoted description'": (
                "single's quoted description",
                "single's quoted description",
            ),
            '"double quoted description"': (
                "double quoted description",
                "double quoted description",
            ),
            ">\n  Folded description across\n  two lines.": (
                "Folded description across two lines.\n",
                "Folded description across two lines.",
            ),
            "|\n  Literal description across\n  two lines.": (
                "Literal description across\ntwo lines.\n",
                "Literal description across\ntwo lines.",
            ),
        }

        for scalar, (expected, stripped) in cases.items():
            with self.subTest(scalar=scalar):
                document = f"---\nname: sample\ndescription: {scalar}\n---\n\n# Body\n"
                parsed = parse_skill_document(document)
                self.assertEqual("sample", parsed.name)
                self.assertEqual(expected, parsed.description)
                self.assertEqual(stripped, parsed.description.rstrip("\n"))
                self.assertEqual("\n# Body\n", parsed.body)

    def test_render_removes_extra_source_frontmatter_and_preserves_body(self):
        source = (
            "---\nname: sample\ndescription: Useful skill.\n"
            "allowed-tools: Bash, Read\nuser-invocable: true\n"
            "metadata:\n  openclaw:\n    requires:\n      bins: [sample]\n---\n"
            "\n# Body\nBody contents.\n"
        )

        parsed = parse_skill_document(source)
        rendered = render_skill_document(parsed)

        self.assertEqual(
            '---\nname: "sample"\ndescription: "Useful skill."\n---\n'
            "\n# Body\nBody contents.\n",
            rendered,
        )
        self.assertNotIn("allowed-tools", rendered)
        self.assertNotIn("user-invocable", rendered)

    def test_literal_description_uses_default_clip_chomping(self):
        parsed = parse_skill_document(
            "---\nname: sample\ndescription: |\n  Literal line.\n\n\n---\nbody\n"
        )

        self.assertEqual("Literal line.\n", parsed.description)

    def test_folded_description_uses_one_newline_for_one_blank_line(self):
        parsed = parse_skill_document(
            "---\nname: sample\ndescription: >\n  first\n\n  second\n---\nbody\n"
        )

        self.assertEqual("first\nsecond\n", parsed.description)

    def test_folded_description_preserves_more_indented_lines(self):
        parsed = parse_skill_document(
            "---\nname: sample\ndescription: >\n"
            "  first\n    command\n  last\n---\nbody\n"
        )

        self.assertEqual("first\n  command\nlast\n", parsed.description)

    def test_parses_agent_reach_folded_description_exactly(self):
        parsed = parse_skill_document(
            (REPOSITORY_ROOT / "agent-reach" / "SKILL.md").read_text(encoding="utf-8")
        )

        self.assertEqual(
            "MUST USE when user wants to research/search/look up/find anything on the "
            'internet — e.g. "research this topic", "do a deep dive on X", "search the '
            'web for X", "see what people say about X", "look this up".\n'
            "Also MUST USE when user mentions any platform or shares any URL/link: "
            "Twitter/X, Reddit, Facebook, Instagram, YouTube, GitHub, Bilibili, XiaoHongShu, "
            "Xiaoyuzhou Podcast, LinkedIn/jobs/recruiting, V2EX, Xueqiu (stocks), RSS.\n"
            "15 platforms, multi-backend routing (OpenCLI / per-platform CLIs / APIs). "
            "Zero config for 6 channels. Run `agent-reach doctor --json` to see which "
            "backend serves each platform right now.\n"
            "NOT for: writing reports/analysis/translation (this skill only FETCHES "
            "internet content); posting/commenting/liking (write operations); platforms "
            "that already have a dedicated skill installed (prefer that skill).\n",
            parsed.description,
        )

    def test_rejects_missing_empty_malformed_and_unsafe_frontmatter(self):
        invalid = {
            "missing opening delimiter": "name: sample\ndescription: useful\n---\nbody",
            "missing closing delimiter": "---\nname: sample\ndescription: useful\nbody",
            "missing name": "---\ndescription: useful\n---\nbody",
            "missing description": "---\nname: sample\n---\nbody",
            "empty description": "---\nname: sample\ndescription: ''\n---\nbody",
            "unsafe name": "---\nname: ../sample\ndescription: useful\n---\nbody",
            "malformed field": "---\nname sample\ndescription: useful\n---\nbody",
            "unterminated quote": "---\nname: sample\ndescription: \"useful\n---\nbody",
            "single quote trailing tokens": (
                "---\nname: sample\ndescription: 'quoted' trailing'\n---\nbody"
            ),
            "undoubled interior single quote": (
                "---\nname: sample\ndescription: 'quoted's invalid'\n---\nbody"
            ),
        }

        for label, document in invalid.items():
            with self.subTest(label=label):
                with self.assertRaises(ValueError):
                    parse_skill_document(document)


class BuildTests(unittest.TestCase):
    def setUp(self):
        test_registry = dict(ADAPTER_REGISTRY)
        for name in ("sample", "source-name", "alpha", "zeta"):
            test_registry[name] = AdapterSpec("native", ())
        self.adapter_registry_patcher = patch(
            "scripts.adapt.ADAPTER_REGISTRY", test_registry
        )
        self.adapter_registry_patcher.start()
        self.repository = tempfile.TemporaryDirectory()
        self.output_parent = tempfile.TemporaryDirectory()
        self.repo_root = Path(self.repository.name)
        self.output = Path(self.output_parent.name) / "skills"

    def tearDown(self):
        self.adapter_registry_patcher.stop()
        self.output_parent.cleanup()
        self.repository.cleanup()

    def make_skill(self, name="sample", description="A useful sample skill."):
        skill = self.repo_root / name
        skill.mkdir(parents=True)
        (skill / "SKILL.md").write_text(
            f"---\nname: {name}\ndescription: {description}\n---\n\n# {name}\n",
            encoding="utf-8",
        )
        return skill

    def test_build_normalizes_document_and_generates_interface_metadata(self):
        skill = self.make_skill(description='"Use a sample: safely."')
        (skill / "SKILL.md").write_text(
            "---\nname: sample\ndescription: \"Use a sample: safely.\"\n"
            "meta: remove me\n---\n\n# Sample\n",
            encoding="utf-8",
        )

        result = build_collection(self.repo_root, manifest(entry()), self.output)

        self.assertEqual(("sample",), result.built_names)
        self.assertEqual(self.output.resolve(), result.output_dir)
        generated = (self.output / "sample" / "SKILL.md").read_text(encoding="utf-8")
        self.assertEqual(
            '---\nname: "sample"\ndescription: "Use a sample: safely."\n'
            "---\n\n# Sample\n",
            generated,
        )
        metadata = (self.output / "sample" / "agents" / "openai.yaml").read_text(
            encoding="utf-8"
        )
        self.assertEqual(
            {
                "interface": {
                    "display_name": "Sample",
                    "short_description": "Use a sample: safely with Sample.",
                    "default_prompt": (
                        "Use $sample to handle this request using its documented workflow."
                    ),
                }
            },
            self.parse_generated_yaml(metadata),
        )
        short_description = self.parse_generated_yaml(metadata)["interface"][
            "short_description"
        ]
        self.assertGreaterEqual(len(short_description), 25)
        self.assertLessEqual(len(short_description), 64)
        self.assertTrue((self.output / ".codex-skills-generated").is_file())

    def test_build_rejects_an_unknown_native_source_adapter(self):
        self.make_skill("unknown-native")

        with self.assertRaisesRegex(KeyError, "unknown Codex adapter"):
            build_collection(
                self.repo_root,
                manifest(entry("unknown-native")),
                self.output,
            )

    def test_allows_only_canonical_output_inside_repository(self):
        self.make_skill()
        canonical = self.repo_root / "codex-skills" / "skills"
        canonical.parent.mkdir()

        result = build_collection(self.repo_root, manifest(entry()), canonical)

        self.assertEqual(canonical.resolve(), result.output_dir)
        self.assertTrue((canonical / ".codex-skills-generated").is_file())

    def test_rejects_git_and_docs_outputs_without_deleting_contents(self):
        self.make_skill()
        for relative in (".git", "docs"):
            with self.subTest(relative=relative):
                output = self.repo_root / relative
                output.mkdir()
                sentinel = output / "sentinel.txt"
                sentinel.write_text("keep\n", encoding="utf-8")

                with self.assertRaisesRegex(ValueError, "canonical"):
                    build_collection(self.repo_root, manifest(entry()), output)

                self.assertEqual("keep\n", sentinel.read_text(encoding="utf-8"))

    def test_rejects_expanded_tilde_output_symlink(self):
        self.make_skill()
        fake_home = Path(self.output_parent.name) / "home"
        fake_home.mkdir()
        target = Path(self.output_parent.name) / "target"
        target.mkdir()
        (fake_home / "output").symlink_to(target, target_is_directory=True)

        with patch.dict(os.environ, {"HOME": str(fake_home)}):
            with self.assertRaisesRegex(ValueError, "symlink"):
                build_collection(self.repo_root, manifest(entry()), Path("~/output"))

        self.assertEqual([], list(target.iterdir()))

    def test_rejects_unowned_nonempty_external_output(self):
        self.make_skill()
        self.output.mkdir()
        sentinel = self.output / "sentinel.txt"
        sentinel.write_text("keep\n", encoding="utf-8")

        with self.assertRaisesRegex(ValueError, "not builder-owned"):
            build_collection(self.repo_root, manifest(entry()), self.output)

        self.assertEqual("keep\n", sentinel.read_text(encoding="utf-8"))

    def test_preserves_old_generated_output_when_staged_copy_fails(self):
        skill = self.make_skill()
        resource = skill / "resource.txt"
        resource.write_text("first\n", encoding="utf-8")
        build_collection(self.repo_root, manifest(entry()), self.output)
        before = self.snapshot(self.output)
        resource.write_text("second\n", encoding="utf-8")

        with patch("scripts.build._copy_resource", side_effect=OSError("copy failed")):
            with self.assertRaisesRegex(OSError, "copy failed"):
                build_collection(self.repo_root, manifest(entry()), self.output)

        self.assertEqual(before, self.snapshot(self.output))

    def test_staged_copy_failure_survives_python311_cleanup_without_leak(self):
        skill = self.make_skill()
        (skill / "resource.txt").write_text("resource\n", encoding="utf-8")
        real_rmtree = shutil.rmtree

        def python311_rmtree(path, ignore_errors=False, onerror=None):
            return real_rmtree(path, ignore_errors=ignore_errors, onerror=onerror)

        with (
            patch("scripts.build._copy_resource", side_effect=OSError("copy exploded")),
            patch("scripts.build.shutil.rmtree", side_effect=python311_rmtree),
        ):
            with self.assertRaisesRegex(OSError, "copy exploded"):
                build_collection(self.repo_root, manifest(entry()), self.output)

        self.assertEqual(
            [], list(self.output.parent.glob(f".{self.output.name}.staging-*"))
        )

    def test_backup_cleanup_failure_returns_warning_after_commit(self):
        skill = self.make_skill()
        resource = skill / "resource.txt"
        resource.write_text("old output\n", encoding="utf-8")
        build_collection(self.repo_root, manifest(entry()), self.output)
        resource.write_text("new output\n", encoding="utf-8")

        with patch(
            "scripts.build._remove_generated_tree",
            side_effect=OSError("cleanup denied"),
        ):
            result = build_collection(self.repo_root, manifest(entry()), self.output)

        backups = list(self.output.parent.glob(f".{self.output.name}.backup-*"))
        self.assertEqual(("sample",), result.built_names)
        self.assertEqual(1, len(result.warnings))
        self.assertIn("cleanup denied", result.warnings[0])
        self.assertIn(backups[0].name, result.warnings[0])
        self.assertEqual(
            "new output\n",
            (self.output / "sample" / "resource.txt").read_text(encoding="utf-8"),
        )
        self.assertEqual(
            "old output\n",
            (backups[0] / "sample" / "resource.txt").read_text(encoding="utf-8"),
        )

    def test_cli_prints_build_warnings_to_stderr_and_returns_success(self):
        result = BuildResult(
            output_dir=self.output.resolve(),
            built_names=("sample",),
            warnings=("orphan backup retained",),
        )
        stdout = io.StringIO()
        stderr = io.StringIO()

        with (
            patch("scripts.build.load_manifest", return_value=manifest(entry())),
            patch("scripts.build.build_collection", return_value=result),
            redirect_stdout(stdout),
            redirect_stderr(stderr),
        ):
            exit_code = main(
                ["--repo", str(self.repo_root), "--output", str(self.output)]
            )

        self.assertEqual(0, exit_code)
        self.assertIn("Built 1 skills", stdout.getvalue())
        self.assertIn("orphan backup retained", stderr.getvalue())

    def test_display_name_comes_from_hyphenated_output_name(self):
        self.make_skill("source-name", "A sufficiently useful source description.")

        build_collection(
            self.repo_root,
            manifest(entry("source-name", "codex-ui-skill")),
            self.output,
        )

        metadata = self.parse_generated_yaml(
            (self.output / "codex-ui-skill" / "agents" / "openai.yaml").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual("Codex Ui Skill", metadata["interface"]["display_name"])
        self.assertIn("$codex-ui-skill", metadata["interface"]["default_prompt"])

    def test_copies_resources_recursively_and_preserves_executable_bit(self):
        skill = self.make_skill()
        script = skill / "scripts" / "run.sh"
        script.parent.mkdir()
        script.write_text("#!/bin/sh\necho okay\n", encoding="utf-8")
        script.chmod(0o755)
        reference = skill / "references" / "guide.md"
        reference.parent.mkdir()
        reference.write_text("guide\n", encoding="utf-8")

        build_collection(self.repo_root, manifest(entry()), self.output)

        copied_script = self.output / "sample" / "scripts" / "run.sh"
        self.assertEqual("guide\n", (self.output / "sample" / "references" / "guide.md").read_text())
        self.assertTrue(copied_script.stat().st_mode & stat.S_IXUSR)

    def test_populates_read_only_resource_directory_before_preserving_mode(self):
        skill = self.make_skill()
        read_only = skill / "references"
        read_only.mkdir()
        (read_only / "guide.md").write_text("guide\n", encoding="utf-8")
        read_only.chmod(0o555)
        try:
            build_collection(self.repo_root, manifest(entry()), self.output)
        finally:
            read_only.chmod(0o755)

        copied = self.output / "sample" / "references"
        self.assertEqual("guide\n", (copied / "guide.md").read_text(encoding="utf-8"))
        self.assertEqual(0o555, stat.S_IMODE(copied.stat().st_mode))

    def test_second_build_cleans_backup_with_read_only_resource_directory(self):
        skill = self.make_skill()
        read_only = skill / "references"
        read_only.mkdir()
        (read_only / "guide.md").write_text("guide\n", encoding="utf-8")
        read_only.chmod(0o555)
        try:
            first = build_collection(self.repo_root, manifest(entry()), self.output)
            second = build_collection(self.repo_root, manifest(entry()), self.output)
        finally:
            read_only.chmod(0o755)

        self.assertEqual((), first.warnings)
        self.assertEqual((), second.warnings)
        self.assertEqual(
            0o555,
            stat.S_IMODE(
                (self.output / "sample" / "references").stat().st_mode
            ),
        )
        self.assertEqual(
            [], list(self.output.parent.glob(f".{self.output.name}.backup-*"))
        )
        self.assertEqual(
            [], list(self.output.parent.glob(f".{self.output.name}.staging-*"))
        )

    def test_excludes_generated_metadata_and_runtime_or_cache_files(self):
        skill = self.make_skill()
        excluded_files = (
            "agents/openai.yaml",
            ".DS_Store",
            "debug.log",
            "module.pyc",
            "__pycache__/module.py",
            ".herenow/state.json",
            ".gstack/state.json",
            ".cache/state.json",
            ".ruff_cache/state.json",
            "nested/cache/state.json",
            "nested/runtime/state.json",
            ".git/config",
        )
        for relative in excluded_files:
            path = skill / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("source state\n", encoding="utf-8")

        build_collection(self.repo_root, manifest(entry()), self.output)

        built = self.output / "sample"
        self.assertTrue((built / "agents" / "openai.yaml").is_file())
        for relative in excluded_files[1:]:
            with self.subTest(relative=relative):
                self.assertFalse((built / relative).exists())

    def test_rejects_source_name_mismatch_with_folder_or_manifest(self):
        skill = self.make_skill()
        (skill / "SKILL.md").write_text(
            "---\nname: different\ndescription: Useful.\n---\nbody\n",
            encoding="utf-8",
        )

        with self.assertRaisesRegex(ValueError, "does not match"):
            build_collection(self.repo_root, manifest(entry()), self.output)

    def test_rejects_symlink_that_escapes_source_skill(self):
        skill = self.make_skill()
        outside = self.repo_root / "outside.txt"
        outside.write_text("secret\n", encoding="utf-8")
        (skill / "escape").symlink_to(outside)

        with self.assertRaisesRegex(ValueError, "unsafe symlink"):
            build_collection(self.repo_root, manifest(entry()), self.output)
        self.assertFalse(self.output.exists())

    def test_rejects_skill_document_symlink_that_escapes_source_skill(self):
        skill = self.repo_root / "sample"
        skill.mkdir()
        outside = self.repo_root / "outside-skill.md"
        outside.write_text(
            "---\nname: sample\ndescription: Outside source.\n---\nbody\n",
            encoding="utf-8",
        )
        (skill / "SKILL.md").symlink_to(outside)

        with self.assertRaisesRegex(ValueError, "unsafe symlink"):
            build_collection(self.repo_root, manifest(entry()), self.output)
        self.assertFalse(self.output.exists())

    def test_preserves_safe_internal_symlink_without_following_it(self):
        skill = self.make_skill()
        (skill / "target.txt").write_text("target\n", encoding="utf-8")
        (skill / "alias.txt").symlink_to("target.txt")

        build_collection(self.repo_root, manifest(entry()), self.output)

        copied = self.output / "sample" / "alias.txt"
        self.assertTrue(copied.is_symlink())
        self.assertEqual("target.txt", os.readlink(copied))
        self.assertTrue(copied.resolve().is_relative_to(self.output.resolve() / "sample"))
        self.assertEqual(b"target\n", copied.resolve().read_bytes())

    def test_rejects_symlink_to_excluded_runtime_directory(self):
        skill = self.make_skill()
        runtime = skill / "runtime"
        runtime.mkdir()
        (runtime / "state.json").write_text("state\n", encoding="utf-8")
        (skill / "runtime-link").symlink_to("runtime", target_is_directory=True)

        with self.assertRaisesRegex(ValueError, "excluded"):
            build_collection(self.repo_root, manifest(entry()), self.output)
        self.assertFalse(self.output.exists())

    def test_rejects_symlink_to_replaced_source_openai_metadata(self):
        skill = self.make_skill()
        source_metadata = skill / "agents" / "openai.yaml"
        source_metadata.parent.mkdir()
        source_metadata.write_text("source metadata\n", encoding="utf-8")
        (skill / "metadata-link").symlink_to("agents/openai.yaml")

        with self.assertRaisesRegex(ValueError, "excluded"):
            build_collection(self.repo_root, manifest(entry()), self.output)
        self.assertFalse(self.output.exists())

    def test_rejects_absolute_symlink_even_when_target_is_internal(self):
        skill = self.make_skill()
        target = skill / "target.txt"
        target.write_text("target\n", encoding="utf-8")
        (skill / "absolute-alias.txt").symlink_to(target.resolve())

        with self.assertRaisesRegex(ValueError, "absolute symlink"):
            build_collection(self.repo_root, manifest(entry()), self.output)
        self.assertFalse(self.output.exists())

    def test_rejects_output_equal_to_root_or_overlapping_source(self):
        skill = self.make_skill()
        unsafe_paths = (
            self.repo_root,
            skill,
            skill / "generated",
            self.repo_root.parent,
        )

        for output in unsafe_paths:
            with self.subTest(output=output):
                with self.assertRaisesRegex(ValueError, "unsafe output"):
                    build_collection(self.repo_root, manifest(entry()), output)

    def test_rejects_archive_output_before_deleting_protected_sources(self):
        self.make_skill()
        archive = self.repo_root / ".agents-backup"
        archive.mkdir()
        archived_file = archive / "archived.md"
        archived_file.write_text("protected archive\n", encoding="utf-8")
        collection = Manifest(
            sources=(entry(),),
            promoted=(promoted_entry(),),
        )
        before = hash_protected_sources(self.repo_root)

        with self.assertRaisesRegex(ValueError, "unsafe output"):
            build_collection(self.repo_root, collection, archive)

        self.assertEqual(before, hash_protected_sources(self.repo_root))
        self.assertEqual("protected archive\n", archived_file.read_text(encoding="utf-8"))

    def test_rejects_output_containing_promoted_provenance_outside_archive(self):
        self.make_skill()
        provenance_dir = self.repo_root / "promoted-input"
        provenance_dir.mkdir()
        provenance = provenance_dir / "source.md"
        provenance.write_text("promoted source\n", encoding="utf-8")
        collection = Manifest(
            sources=(entry(),),
            promoted=(
                promoted_entry(provenance="promoted-input/source.md"),
            ),
        )

        with self.assertRaisesRegex(ValueError, "unsafe output"):
            build_collection(self.repo_root, collection, provenance_dir)

        self.assertEqual("promoted source\n", provenance.read_text(encoding="utf-8"))

    def test_rebuild_is_deterministic_and_removes_stale_files(self):
        self.make_skill("zeta", "Zeta performs a deterministic task.")
        self.make_skill("alpha", "Alpha performs a deterministic task.")
        collection = manifest(entry("zeta"), entry("alpha"))

        first = build_collection(self.repo_root, collection, self.output)
        first_snapshot = self.snapshot(self.output)
        stale = self.output / "stale.txt"
        stale.write_text("stale\n", encoding="utf-8")
        second = build_collection(self.repo_root, collection, self.output)

        self.assertEqual(("alpha", "zeta"), first.built_names)
        self.assertEqual(first, second)
        self.assertEqual(first_snapshot, self.snapshot(self.output))
        self.assertFalse(stale.exists())
        self.assertEqual(
            [], list(self.output.parent.glob(f".{self.output.name}.backup-*"))
        )

    def test_build_does_not_mutate_source_files(self):
        skill = self.make_skill()
        resource = skill / "resource.txt"
        resource.write_text("original\n", encoding="utf-8")
        before = self.snapshot(skill, follow_symlinks=False)

        build_collection(self.repo_root, manifest(entry()), self.output)

        self.assertEqual(before, self.snapshot(skill, follow_symlinks=False))

    def test_preserves_crlf_body_bytes_deterministically(self):
        skill = self.repo_root / "sample"
        skill.mkdir()
        (skill / "SKILL.md").write_bytes(
            b"---\r\nname: sample\r\ndescription: Useful skill.\r\n---\r\n"
            b"\r\n# Body\r\nBody contents.\r\n"
        )
        expected = (
            b'---\nname: "sample"\ndescription: "Useful skill."\n---\n'
            b"\r\n# Body\r\nBody contents.\r\n"
        )

        build_collection(self.repo_root, manifest(entry()), self.output)
        first = (self.output / "sample" / "SKILL.md").read_bytes()
        metadata = (self.output / "sample" / "agents" / "openai.yaml").read_bytes()
        build_collection(self.repo_root, manifest(entry()), self.output)
        second = (self.output / "sample" / "SKILL.md").read_bytes()

        self.assertEqual(expected, first)
        self.assertNotIn(b"\r\r\n", first)
        self.assertNotIn(b"\r", metadata)
        self.assertEqual(first, second)

    @staticmethod
    def parse_generated_yaml(text):
        lines = text.splitlines()
        result = {"interface": {}}
        for line in lines[1:]:
            key, value = line.strip().split(": ", 1)
            result["interface"][key] = json.loads(value)
        return result

    @staticmethod
    def snapshot(root, follow_symlinks=True):
        snapshot = {}
        for path in sorted(root.rglob("*")):
            relative = path.relative_to(root).as_posix()
            if path.is_symlink() and not follow_symlinks:
                snapshot[relative] = ("symlink", os.readlink(path))
            elif path.is_file():
                snapshot[relative] = (path.read_bytes(), stat.S_IMODE(path.stat().st_mode))
            elif path.is_dir():
                snapshot[relative] = "directory"
        return snapshot


if __name__ == "__main__":
    unittest.main()
