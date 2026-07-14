import hashlib
import json
import shutil
import tempfile
import unittest
from collections import Counter
from pathlib import Path

from scripts.adapt import ADAPTER_REGISTRY, validate_generated_markdown
from scripts.build import build_collection
from scripts.common import (
    Manifest,
    discover_source_skills,
    hash_protected_sources,
    load_manifest,
    parse_skill_document,
)
from scripts.legacy_integrity import (
    LEGACY_ARCHIVED_SOURCE_SHA256,
    LEGACY_PROMOTED_INPUT_SHA256,
    LEGACY_PROMOTED_PROVENANCE,
)
from scripts.validate import validate_collection


CODEX_SKILLS_ROOT = Path(__file__).resolve().parents[1]
REPOSITORY_ROOT = CODEX_SKILLS_ROOT.parent
MANIFEST_PATH = CODEX_SKILLS_ROOT / "manifest.yaml"

LEGACY_GITNEXUS = frozenset(LEGACY_PROMOTED_PROVENANCE)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class SourceTopologyTests(unittest.TestCase):
    def test_current_active_shelf_and_manifest_have_exact_59_output_topology(self):
        manifest = load_manifest(MANIFEST_PATH, repo_root=REPOSITORY_ROOT)
        active = {path.name for path in discover_source_skills(REPOSITORY_ROOT)}

        self.assertEqual(45, len(active))
        self.assertIn("graphify", active)
        self.assertTrue(active.isdisjoint(LEGACY_GITNEXUS))
        self.assertEqual(active, {entry.source for entry in manifest.sources})
        self.assertEqual(14, len(manifest.promoted))
        self.assertEqual(59, len(manifest.entries))
        self.assertEqual(
            Counter({"dependency-required": 44, "adapted": 9, "native": 6}),
            Counter(entry.conversion for entry in manifest.entries),
        )

    def test_source_snapshot_is_exact_current_241_file_active_shelf(self):
        current = hash_protected_sources(REPOSITORY_ROOT)
        snapshot = json.loads(
            (CODEX_SKILLS_ROOT / "source-hashes.json").read_text(encoding="utf-8")
        )

        self.assertEqual(241, len(current))
        self.assertEqual(current, snapshot)
        self.assertTrue(any(path.startswith("graphify/") for path in snapshot))
        self.assertFalse(any(path.startswith("gitnexus-") for path in snapshot))


class LegacyGitNexusTests(unittest.TestCase):
    def test_archived_sources_and_promoted_inputs_preserve_exact_prior_bytes(self):
        manifest = load_manifest(MANIFEST_PATH, repo_root=REPOSITORY_ROOT)
        entries = {entry.output: entry for entry in manifest.promoted}

        for name in sorted(LEGACY_GITNEXUS):
            with self.subTest(name=name):
                provenance = LEGACY_PROMOTED_PROVENANCE[name]
                self.assertEqual(provenance, entries[name].promoted_from)
                self.assertEqual("dependency-required", entries[name].conversion)
                self.assertEqual(
                    LEGACY_ARCHIVED_SOURCE_SHA256[name],
                    digest(REPOSITORY_ROOT / provenance),
                )
                promoted = CODEX_SKILLS_ROOT / "promoted" / name / "SKILL.md"
                self.assertEqual(LEGACY_PROMOTED_INPUT_SHA256[name], digest(promoted))
                self.assertEqual(name, parse_skill_document(promoted.read_text()).name)

    def make_legacy_build_fixture(self, root: Path, name: str):
        provenance = LEGACY_PROMOTED_PROVENANCE[name]
        archive = root / provenance
        archive.parent.mkdir(parents=True)
        shutil.copy2(REPOSITORY_ROOT / provenance, archive)
        promoted = root / "codex-skills" / "promoted" / name
        shutil.copytree(CODEX_SKILLS_ROOT / "promoted" / name, promoted)
        manifest = load_manifest(MANIFEST_PATH, repo_root=REPOSITORY_ROOT)
        entry = next(entry for entry in manifest.promoted if entry.output == name)
        return archive, promoted / "SKILL.md", Manifest((), (entry,))

    def make_legacy_validation_fixture(self, root: Path):
        (root / "codex-skills").mkdir()
        shutil.copy2(MANIFEST_PATH, root / "codex-skills" / "manifest.yaml")
        shutil.copytree(
            CODEX_SKILLS_ROOT / "archived-sources",
            root / "codex-skills" / "archived-sources",
        )
        shutil.copytree(
            CODEX_SKILLS_ROOT / "promoted",
            root / "codex-skills" / "promoted",
        )
        shutil.copytree(REPOSITORY_ROOT / ".agents-backup", root / ".agents-backup")
        for source in discover_source_skills(REPOSITORY_ROOT):
            shutil.copytree(source, root / source.name)
        snapshot = hash_protected_sources(root)
        (root / "codex-skills" / "source-hashes.json").write_text(
            json.dumps(snapshot, indent=2) + "\n",
            encoding="utf-8",
        )

    def test_real_build_rejects_tampered_legacy_archive_and_promoted_input(self):
        cases = (
            ("archive", "legacy archived source digest mismatch"),
            ("promoted", "legacy promoted input digest mismatch"),
            ("promoted-tree", "legacy promoted input tree mismatch"),
        )
        for target, expected in cases:
            with self.subTest(target=target), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary) / "repo"
                root.mkdir()
                archive, promoted, manifest = self.make_legacy_build_fixture(
                    root, "gitnexus-cli"
                )
                if target == "promoted-tree":
                    promoted.parent.joinpath("unexpected.md").write_text(
                        "unexpected\n", encoding="utf-8"
                    )
                else:
                    tampered = archive if target == "archive" else promoted
                    tampered.write_bytes(tampered.read_bytes() + b"\nreview tamper\n")

                with self.assertRaisesRegex(ValueError, expected):
                    build_collection(root, manifest, Path(temporary) / "output")

    def test_real_validation_rejects_tampered_legacy_archive_and_promoted_input(self):
        cases = (
            ("archive", "legacy archived source digest mismatch"),
            ("promoted", "legacy promoted input digest mismatch"),
            ("promoted-tree", "legacy promoted input tree mismatch"),
        )
        for target, expected in cases:
            with self.subTest(target=target), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary) / "repo"
                root.mkdir()
                self.make_legacy_validation_fixture(root)
                if target == "promoted-tree":
                    root.joinpath(
                        "codex-skills/promoted/gitnexus-cli/unexpected.md"
                    ).write_text("unexpected\n", encoding="utf-8")
                    tampered = None
                elif target == "archive":
                    tampered = root / LEGACY_PROMOTED_PROVENANCE["gitnexus-cli"]
                else:
                    tampered = (
                        root
                        / "codex-skills/promoted/gitnexus-cli/SKILL.md"
                    )
                if tampered is not None:
                    tampered.write_bytes(tampered.read_bytes() + b"\nreview tamper\n")

                report = validate_collection(root, source_only=True)

                self.assertFalse(report.ok)
                self.assertTrue(
                    any(expected in error for error in report.errors), report.errors
                )

    def test_dependency_required_promoted_contract_is_strictly_supported(self):
        name = "gitnexus-cli"
        dependencies = ("GitNexus CLI or MCP", "indexed Git repository")
        with tempfile.TemporaryDirectory() as temporary:
            repo = Path(temporary) / "repo"
            repo.mkdir()
            _, _, manifest = self.make_legacy_build_fixture(repo, name)
            entry = manifest.promoted[0]
            output = Path(temporary) / "output"

            result = build_collection(repo, manifest, output)

            self.assertEqual((name,), result.built_names)
            self.assertEqual(dependencies, entry.dependencies)


class GraphifyAdaptationTests(unittest.TestCase):
    def test_graphify_is_dependency_required_with_mandatory_runtime_inputs(self):
        manifest = load_manifest(MANIFEST_PATH, repo_root=REPOSITORY_ROOT)
        entry = next(entry for entry in manifest.sources if entry.output == "graphify")

        self.assertEqual("dependency-required", entry.conversion)
        self.assertEqual(
            (
                "Python 3 with graphifyy installed or package-install access",
                "read/write access to the target corpus and graphify-out",
            ),
            entry.dependencies,
        )
        self.assertEqual(
            (entry.conversion, entry.dependencies),
            (ADAPTER_REGISTRY["graphify"].conversion, ADAPTER_REGISTRY["graphify"].dependencies),
        )

    def test_graphify_adapter_preserves_resources_and_removes_active_claude_runtime(self):
        manifest = load_manifest(MANIFEST_PATH, repo_root=REPOSITORY_ROOT)
        source_resources = {
            path.relative_to(REPOSITORY_ROOT / "graphify").as_posix()
            for path in (REPOSITORY_ROOT / "graphify").rglob("*")
            if path.is_file() and path.name != "SKILL.md"
        }
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "skills"
            build_collection(REPOSITORY_ROOT, manifest, output)
            generated = output / "graphify"
            generated_resources = {
                path.relative_to(generated).as_posix()
                for path in generated.rglob("*")
                if path.is_file()
                and path.name not in {"SKILL.md", "openai.yaml"}
            }
            skill_text = (generated / "SKILL.md").read_text(encoding="utf-8")
            all_markdown = "\n".join(
                path.read_text(encoding="utf-8")
                for path in sorted(generated.rglob("*.md"))
            )

        self.assertEqual(source_resources, generated_resources)
        self.assertIn("$graphify --help", skill_text)
        self.assertIn("graphify query", skill_text)
        self.assertIn("references/query.md", skill_text)
        self.assertIn("collaboration is available", skill_text)
        self.assertIn("process each chunk directly", skill_text)
        self.assertNotRegex(all_markdown, r"(?<![\w.-])/graphify(?=\s|$)")
        self.assertNotRegex(all_markdown, r"(?i)claude|Agent tool|Write tool")
        self.assertNotRegex(
            all_markdown,
            r"subagent_type|Explore type|general-purpose agent|must use collaboration",
        )
        validate_generated_markdown("graphify", "SKILL.md", skill_text)


class LibrarianSyncAdaptationTests(unittest.TestCase):
    def test_librarian_helper_audits_codex_shelf_and_gates_parallel_repo_sync(self):
        helper = CODEX_SKILLS_ROOT / "adapters" / "skills-librarian" / "audit.py"
        text = helper.read_text(encoding="utf-8")

        self.assertIn('~/.codex/skills', text)
        self.assertIn('CODEX_SKILLS_REPO', text)
        self.assertIn('origin/main', text)
        self.assertIn('SHELF IS STALE', text)
        self.assertIn('SKILLS_NO_FETCH', text)
        self.assertIn('upstream freshness is unverified', text)
        self.assertNotIn('~/.claude/skills', text)

    def test_librarian_skill_preserves_agents_source_and_parallel_mirror_contract(self):
        text = (CODEX_SKILLS_ROOT / "overrides" / "skills-librarian" / "SKILL.md").read_text(
            encoding="utf-8"
        )

        self.assertIn('AGENTS_SRC="$HOME/.agents"', text)
        self.assertIn('CODEX_SKILLS_REPO', text)
        self.assertIn('origin/main', text)
        self.assertIn('stale', text.casefold())
        self.assertIn('unverified', text.casefold())


if __name__ == "__main__":
    unittest.main()
