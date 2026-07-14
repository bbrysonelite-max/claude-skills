import hashlib
import json
import tempfile
import unittest
from collections import Counter
from pathlib import Path
from unittest.mock import patch

from scripts.adapt import ADAPTER_REGISTRY, validate_generated_markdown
from scripts.build import PROMOTED_PROVENANCE, build_collection
from scripts.common import (
    Manifest,
    SkillEntry,
    discover_source_skills,
    hash_protected_sources,
    load_manifest,
    parse_skill_document,
)


CODEX_SKILLS_ROOT = Path(__file__).resolve().parents[1]
REPOSITORY_ROOT = CODEX_SKILLS_ROOT.parent
MANIFEST_PATH = CODEX_SKILLS_ROOT / "manifest.yaml"

LEGACY_GITNEXUS = {
    "gitnexus-cli": (
        "a699a9dd168a68e7357b1704be0ff5ceee30b2a348042789355cca171c060e02",
        "71d686d81713621d9df050e85faedec51749fea88488fc880b681d5876fb0706",
    ),
    "gitnexus-debugging": (
        "4a1e82aa835c52e38227d853c20ef05ea33be1dfb6aa6511474d15357f1d3f2e",
        "e77115bb0c1b0c38aea2b73c60d79bdc6460b3784dd9f37d44f4b9ba7e926c3c",
    ),
    "gitnexus-exploring": (
        "ffafeaa0ce52be079e4d4b3a48c0a166728c009380a243c394c4e08f728527bb",
        "15af2f5550d327d2d36b8a28e96b5b361dabcfd950d249eeff29af5f80f8ac3d",
    ),
    "gitnexus-guide": (
        "40b047beeb9a7c5d47f17426b4061d2c2562c85c11288fa7f8da376d910e4f91",
        "25814aa095be6dc48cc25f027142d2b524fc2cfa748a5189fdede21a79ab1482",
    ),
    "gitnexus-impact-analysis": (
        "a4d6e8003c4a822c380b0e81b2fa0d642612236c734a9d51834e362c4be52f33",
        "70fbc9d1e1e1e9a81545b20f57a286723e2a4301010f00649edf6e886e307b52",
    ),
    "gitnexus-pr-review": (
        "f7bac200a4752191d2e3aa7a2273720ca436d25df88cb2ef48dc19f92ae0934e",
        "063a613a59fe0bba18a946828738ced39a7f1d7f34bd743a79ee5591c3fd22d5",
    ),
    "gitnexus-refactoring": (
        "6aab994ee0266063245245483ee3280645aca66c0c5e56730ffad3f32ecbbc5c",
        "c26e29e19e908eb2644c682d320a1a2cea77d0714d668d2843d634c14a4300b5",
    ),
}


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

        for name, (source_digest, generated_digest) in LEGACY_GITNEXUS.items():
            with self.subTest(name=name):
                provenance = f"codex-skills/archived-sources/{name}/SKILL.md"
                self.assertEqual(provenance, entries[name].promoted_from)
                self.assertEqual("dependency-required", entries[name].conversion)
                self.assertEqual(source_digest, digest(REPOSITORY_ROOT / provenance))
                promoted = CODEX_SKILLS_ROOT / "promoted" / name / "SKILL.md"
                self.assertEqual(generated_digest, digest(promoted))
                self.assertEqual(name, parse_skill_document(promoted.read_text()).name)

    def test_dependency_required_promoted_contract_is_strictly_supported(self):
        name = "gitnexus-cli"
        provenance = f"codex-skills/archived-sources/{name}/SKILL.md"
        dependencies = ("GitNexus CLI or MCP", "indexed Git repository")
        with tempfile.TemporaryDirectory() as temporary:
            repo = Path(temporary) / "repo"
            source = repo / provenance
            source.parent.mkdir(parents=True)
            source.write_text("archived source\n", encoding="utf-8")
            promoted = repo / "codex-skills" / "promoted" / name
            promoted.mkdir(parents=True)
            promoted.joinpath("SKILL.md").write_text(
                "---\nname: gitnexus-cli\n"
                "description: Use when GitNexus graph operations are requested.\n"
                "---\n\n# GitNexus\n\n## Codex Runtime\n\n"
                "Operate directly in the main Codex agent.\n"
                "Never expose or print secret, credential, or token values.\n\n"
                "Mandatory dependencies:\n"
                "- `GitNexus CLI or MCP`\n"
                "- `indexed Git repository`\n\n"
                "Preflight each dependency using MCP/app capability discovery.\n"
                "If any mandatory dependency is unavailable, stop and report it.\n",
                encoding="utf-8",
            )
            entry = SkillEntry(
                source=None,
                promoted_from=provenance,
                output=name,
                conversion="dependency-required",
                dependencies=dependencies,
                notes="Retained legacy GitNexus workflow.",
            )
            output = Path(temporary) / "output"

            with patch.dict(PROMOTED_PROVENANCE, {name: provenance}, clear=True):
                result = build_collection(repo, Manifest((), (entry,)), output)

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
        self.assertNotIn('~/.claude/skills', text)

    def test_librarian_skill_preserves_agents_source_and_parallel_mirror_contract(self):
        text = (CODEX_SKILLS_ROOT / "overrides" / "skills-librarian" / "SKILL.md").read_text(
            encoding="utf-8"
        )

        self.assertIn('AGENTS_SRC="$HOME/.agents"', text)
        self.assertIn('CODEX_SKILLS_REPO', text)
        self.assertIn('origin/main', text)
        self.assertIn('stale', text.casefold())


if __name__ == "__main__":
    unittest.main()
