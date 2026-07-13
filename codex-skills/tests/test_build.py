import json
import os
import stat
import tempfile
import unittest
from pathlib import Path

from scripts.build import build_collection
from scripts.common import (
    Manifest,
    SkillEntry,
    parse_skill_document,
    render_skill_document,
)


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
        }

        for label, document in invalid.items():
            with self.subTest(label=label):
                with self.assertRaises(ValueError):
                    parse_skill_document(document)


class BuildTests(unittest.TestCase):
    def setUp(self):
        self.repository = tempfile.TemporaryDirectory()
        self.output_parent = tempfile.TemporaryDirectory()
        self.repo_root = Path(self.repository.name)
        self.output = Path(self.output_parent.name) / "skills"

    def tearDown(self):
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

    def test_build_does_not_mutate_source_files(self):
        skill = self.make_skill()
        resource = skill / "resource.txt"
        resource.write_text("original\n", encoding="utf-8")
        before = self.snapshot(skill, follow_symlinks=False)

        build_collection(self.repo_root, manifest(entry()), self.output)

        self.assertEqual(before, self.snapshot(skill, follow_symlinks=False))

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
